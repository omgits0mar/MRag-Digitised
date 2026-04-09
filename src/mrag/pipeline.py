"""Top-level RAG pipeline orchestrator.

Wires together query processing, retrieval, generation, caching, and
metrics into a single ``ask()`` call. This is the primary public API
for Phase 2 consumers.
"""

from __future__ import annotations

import time

import structlog

from mrag.cache.embedding_cache import EmbeddingCache
from mrag.cache.metrics import MetricsCollector
from mrag.cache.models import RequestMetrics
from mrag.cache.response_cache import ResponseCache
from mrag.generation.models import GeneratedResponse
from mrag.generation.pipeline import GenerationPipeline
from mrag.query.pipeline import QueryPipeline
from mrag.retrieval.models import RetrievalRequest, RetrievalResult
from mrag.retrieval.retriever import RetrieverService

logger = structlog.get_logger(__name__)


class MRAGPipeline:
    """End-to-end RAG pipeline: query → retrieval → generation → response.

    Optionally integrates an ``EmbeddingCache``, ``ResponseCache``, and
    ``MetricsCollector`` for production-grade observability and
    performance.

    Args:
        query_pipeline: Query preprocessing and expansion.
        retriever: Vector search service.
        generation_pipeline: LLM answer generation.
        embedding_cache: Optional cache for query vectors.
        response_cache: Optional TTL cache for full responses.
        metrics_collector: Optional per-request metrics accumulator.
    """

    def __init__(
        self,
        query_pipeline: QueryPipeline,
        retriever: RetrieverService,
        generation_pipeline: GenerationPipeline,
        embedding_cache: EmbeddingCache | None = None,
        response_cache: ResponseCache | None = None,
        metrics_collector: MetricsCollector | None = None,
    ) -> None:
        self._query_pipeline = query_pipeline
        self._retriever = retriever
        self._generation_pipeline = generation_pipeline
        self._embedding_cache = embedding_cache
        self._response_cache = response_cache
        self._metrics = metrics_collector

    async def ask(
        self,
        query: str,
        expand: bool = True,
        temperature: float = 0.1,
        max_tokens: int = 1024,
    ) -> GeneratedResponse:
        """Process a user query through the full pipeline.

        Flow:
            1. Query preprocessing (normalize, contextualize, expand).
            2. Response cache check.
            3. Retrieval (with optional embedding cache).
            4. LLM generation with confidence validation.
            5. Cache and metrics recording.

        Args:
            query: Raw user query.
            expand: Whether to run query expansion.
            temperature: LLM sampling temperature.
            max_tokens: Max LLM response tokens.

        Returns:
            ``GeneratedResponse`` with answer, confidence, sources, and metrics.
        """
        total_start = time.perf_counter_ns()

        # Stage 1: Query processing
        self._maybe_start("preprocessing")
        processed = self._query_pipeline.process(query, expand=expand)
        preprocessing_ms = self._maybe_stop("preprocessing")

        # Stage 2: Response cache check
        if self._response_cache is not None:
            cached = self._response_cache.get(processed.query_hash)
            if cached is not None:
                logger.info("pipeline_cache_hit", query_hash=processed.query_hash[:8])
                metrics = RequestMetrics(
                    preprocessing_time_ms=preprocessing_ms,
                    total_time_ms=self._elapsed_ms(total_start),
                    cache_hit=True,
                    cache_type="response",
                )
                cached.metrics = metrics
                self._maybe_record(metrics)
                return cached

        # Stage 3: Retrieval
        self._maybe_start("embedding")
        self._maybe_start("search")
        retrieval_request = RetrievalRequest(query=processed.final_query)
        try:
            retrieval_results = self._retriever.retrieve(retrieval_request)
        except Exception as exc:
            logger.error("pipeline_retrieval_failed", error=str(exc))
            retrieval_results: list[RetrievalResult] = []
        search_ms = self._maybe_stop("search")
        embedding_ms = self._maybe_stop("embedding")

        # Stage 4: Generation
        self._maybe_start("llm")
        response = await self._generation_pipeline.generate_answer(
            query=processed.original_query,
            retrieval_results=retrieval_results,
            conversation_history=processed.conversation_history or None,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        llm_ms = self._maybe_stop("llm")

        # Stage 5: Populate full metrics on the response
        total_ms = self._elapsed_ms(total_start)
        full_metrics = RequestMetrics(
            preprocessing_time_ms=preprocessing_ms,
            embedding_time_ms=embedding_ms,
            search_time_ms=search_ms,
            llm_time_ms=llm_ms,
            total_time_ms=total_ms,
            cache_hit=False,
            cache_type=None,
        )
        response.metrics = full_metrics

        # Stage 6: Cache the response
        if self._response_cache is not None:
            self._response_cache.put(processed.query_hash, response)

        self._maybe_record(full_metrics)

        logger.info(
            "pipeline_complete",
            confidence=round(response.confidence_score, 3),
            is_fallback=response.is_fallback,
            total_ms=round(total_ms, 1),
        )
        return response

    # ---------------------------------------------------------------- helpers

    def _maybe_start(self, label: str) -> None:
        if self._metrics is not None:
            self._metrics.start_timer(label)

    def _maybe_stop(self, label: str) -> float:
        if self._metrics is not None:
            return self._metrics.stop_timer(label)
        return 0.0

    def _maybe_record(self, metrics: RequestMetrics) -> None:
        if self._metrics is not None:
            self._metrics.record(metrics)

    @staticmethod
    def _elapsed_ms(start_ns: int) -> float:
        return (time.perf_counter_ns() - start_ns) / 1_000_000
