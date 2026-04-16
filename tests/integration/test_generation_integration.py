"""Integration test: generation pipeline end-to-end with mocked LLM."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from mrag.generation.fallback import FallbackHandler
from mrag.generation.llm_client import BaseLLMClient
from mrag.generation.pipeline import GenerationPipeline
from mrag.generation.prompt_builder import PromptBuilder
from mrag.generation.validator import ResponseValidator
from mrag.retrieval.models import RetrievalResult


def _chunk(text: str, score: float = 0.85) -> RetrievalResult:
    return RetrievalResult(
        chunk_id="c1",
        doc_id="d1",
        chunk_text=text,
        relevance_score=score,
        cosine_similarity=score,
        question="q",
        answer_short="short",
        answer_long=text,
        question_type="factoid",
        domain="science",
        difficulty="easy",
        has_short_answer=True,
    )


@pytest.fixture()
def generation_pipeline(self) -> GenerationPipeline:  # type: ignore[misc]
    llm = AsyncMock(spec=BaseLLMClient)
    llm.generate = AsyncMock(
        return_value=(
            "Photosynthesis converts light energy into chemical energy"
            " via chlorophyll."
        )
    )
    pb = PromptBuilder(templates_dir="prompts/templates")
    validator = ResponseValidator(confidence_threshold=0.3, alpha=0.6)
    fallback = FallbackHandler(pb)
    return GenerationPipeline(
        llm_client=llm,
        prompt_builder=pb,
        validator=validator,
        fallback_handler=fallback,
    )


@pytest.mark.asyncio
class TestGenerationIntegration:
    async def test_e2e_generation_with_context(self) -> None:
        llm = AsyncMock(spec=BaseLLMClient)
        llm.generate = AsyncMock(
            return_value=(
                "Photosynthesis is a process by which plants convert light "
                "energy into chemical energy via chlorophyll."
            )
        )
        pb = PromptBuilder(templates_dir="prompts/templates")
        validator = ResponseValidator(confidence_threshold=0.3, alpha=0.6)
        fallback = FallbackHandler(pb)
        pipeline = GenerationPipeline(llm, pb, validator, fallback)

        chunks = [
            _chunk(
                "Photosynthesis is a process used by plants to convert light "
                "energy into chemical energy using chlorophyll.",
                0.95,
            ),
        ]
        response = await pipeline.generate_answer(
            query="what is photosynthesis",
            retrieval_results=chunks,
        )

        assert response.is_fallback is False
        assert "photosynthesis" in response.answer.lower()
        assert response.confidence_score > 0.0
        assert len(response.sources) == 1
        assert response.metrics.llm_time_ms >= 0.0
        llm.generate.assert_awaited_once()

    async def test_e2e_fallback_on_no_context(self) -> None:
        llm = AsyncMock(spec=BaseLLMClient)
        pb = PromptBuilder(templates_dir="prompts/templates")
        validator = ResponseValidator(confidence_threshold=0.3)
        fallback = FallbackHandler(pb)
        pipeline = GenerationPipeline(llm, pb, validator, fallback)

        response = await pipeline.generate_answer(
            query="unanswerable question",
            retrieval_results=[],
        )

        assert response.is_fallback is True
        assert response.confidence_score == 0.0
        llm.generate.assert_not_awaited()

    async def test_prompt_contains_context(self) -> None:
        llm = AsyncMock(spec=BaseLLMClient)
        llm.generate = AsyncMock(return_value="Some answer.")

        pb = PromptBuilder(templates_dir="prompts/templates")
        validator = ResponseValidator(confidence_threshold=0.3)
        fallback = FallbackHandler(pb)
        pipeline = GenerationPipeline(llm, pb, validator, fallback)

        chunks = [
            _chunk("DNA is deoxyribonucleic acid that carries genetic instructions."),
        ]
        await pipeline.generate_answer("what is DNA", retrieval_results=chunks)

        call_args = llm.generate.call_args
        prompt_text = (
            call_args.kwargs.get("prompt")
            or call_args[1].get("prompt")
            or call_args[0][0]
        )
        assert "DNA" in prompt_text
