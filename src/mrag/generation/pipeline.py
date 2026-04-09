"""Generation pipeline orchestrator.

Builds a Q&A prompt, calls the LLM, validates the response, and either
returns the grounded answer or a fallback message. Timing information
is captured in ``RequestMetrics``.
"""

from __future__ import annotations

import time

import structlog

from mrag.cache.models import RequestMetrics
from mrag.exceptions import ResponseGenerationError
from mrag.generation.fallback import FallbackHandler
from mrag.generation.llm_client import BaseLLMClient
from mrag.generation.models import GeneratedResponse, SourceCitation
from mrag.generation.prompt_builder import PromptBuilder
from mrag.generation.validator import ResponseValidator
from mrag.query.models import ConversationTurn
from mrag.retrieval.models import RetrievalResult

logger = structlog.get_logger(__name__)


class GenerationPipeline:
    """End-to-end answer generation pipeline.

    Args:
        llm_client: Any ``BaseLLMClient`` implementation.
        prompt_builder: Prompt renderer.
        validator: Confidence scorer.
        fallback_handler: Emits canned responses for low-confidence answers.
    """

    def __init__(
        self,
        llm_client: BaseLLMClient,
        prompt_builder: PromptBuilder,
        validator: ResponseValidator,
        fallback_handler: FallbackHandler,
    ) -> None:
        self._llm_client = llm_client
        self._prompt_builder = prompt_builder
        self._validator = validator
        self._fallback_handler = fallback_handler

    async def generate_answer(
        self,
        query: str,
        retrieval_results: list[RetrievalResult],
        conversation_history: list[ConversationTurn] | None = None,
        temperature: float = 0.1,
        max_tokens: int = 1024,
    ) -> GeneratedResponse:
        """Generate an answer for ``query`` using ``retrieval_results``.

        Flow:
            1. Build the QA + system prompts (or fallback if no context).
            2. Call the LLM.
            3. Validate the response with ``ResponseValidator``.
            4. If confidence is below the threshold, emit a fallback.
            5. Return a ``GeneratedResponse`` with source citations and
               ``RequestMetrics`` (``llm_time_ms`` populated here; the
               top-level pipeline fills in the rest).
        """
        sources = [
            SourceCitation(
                chunk_id=r.chunk_id,
                doc_id=r.doc_id,
                chunk_text=r.chunk_text,
                relevance_score=r.relevance_score,
            )
            for r in retrieval_results
        ]

        # With no retrieved context we short-circuit to the fallback rather
        # than calling the LLM with an empty prompt.
        if not retrieval_results:
            logger.info("generation_skipped_no_context")
            fallback_text = self._fallback_handler.get_fallback_response(query)
            return GeneratedResponse(
                query=query,
                answer=fallback_text,
                confidence_score=0.0,
                is_fallback=True,
                sources=[],
                metrics=RequestMetrics(),
            )

        system_prompt = self._prompt_builder.build_system_prompt()
        qa_prompt = self._prompt_builder.build_qa_prompt(
            query=query,
            context_chunks=retrieval_results,
            conversation_history=conversation_history,
        )

        llm_start = time.perf_counter_ns()
        try:
            answer_text = await self._llm_client.generate(
                prompt=qa_prompt,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except ResponseGenerationError as exc:
            logger.warning("llm_generation_failed", error=str(exc))
            fallback_text = self._fallback_handler.get_fallback_response(query)
            llm_ms = (time.perf_counter_ns() - llm_start) / 1_000_000
            return GeneratedResponse(
                query=query,
                answer=fallback_text,
                confidence_score=0.0,
                is_fallback=True,
                sources=sources,
                metrics=RequestMetrics(llm_time_ms=llm_ms),
            )
        llm_ms = (time.perf_counter_ns() - llm_start) / 1_000_000

        retrieval_scores = [r.relevance_score for r in retrieval_results]
        validation = self._validator.validate(
            response_text=answer_text,
            context_chunks=retrieval_results,
            retrieval_scores=retrieval_scores,
        )

        if not validation.is_confident:
            logger.info(
                "generation_below_threshold_fallback",
                confidence=validation.confidence_score,
                threshold=validation.threshold_used,
            )
            fallback_text = self._fallback_handler.get_fallback_response(query)
            return GeneratedResponse(
                query=query,
                answer=fallback_text,
                confidence_score=validation.confidence_score,
                is_fallback=True,
                sources=sources,
                metrics=RequestMetrics(llm_time_ms=llm_ms),
            )

        logger.info(
            "generation_complete",
            confidence=validation.confidence_score,
            answer_length=len(answer_text or ""),
        )

        return GeneratedResponse(
            query=query,
            answer=answer_text,
            confidence_score=validation.confidence_score,
            is_fallback=False,
            sources=sources,
            metrics=RequestMetrics(llm_time_ms=llm_ms),
        )
