"""Batch query processor for evaluation and benchmarking workloads.

Runs a list of queries through retrieval (+ optional generation) with
per-query error isolation so a single failing query cannot crash the
entire batch. Batch embedding happens inside the retriever, which
already delegates to ``EmbeddingEncoder.encode()``.
"""

from __future__ import annotations

import structlog
from typing import TYPE_CHECKING

from mrag.cache.models import RequestMetrics
from mrag.retrieval.models import RetrievalRequest, RetrievalResult

if TYPE_CHECKING:
    from mrag.generation.models import GeneratedResponse

logger = structlog.get_logger(__name__)


class BatchProcessor:
    """Process multiple queries through retrieval and optional generation.

    Args:
        retriever: Retriever service used for each query.
        generation_pipeline: Optional generation pipeline. Required when
            ``process_batch(..., retrieval_only=False)`` is called.
        batch_size: Soft hint for progress logging intervals.
    """

    def __init__(
        self,
        retriever,  # noqa: ANN001 — RetrieverService (forward reference)
        generation_pipeline=None,  # noqa: ANN001 — GenerationPipeline | None
        batch_size: int = 64,
    ) -> None:
        if batch_size < 1:
            raise ValueError("batch_size must be >= 1")
        self._retriever = retriever
        self._generation_pipeline = generation_pipeline
        self._batch_size = batch_size

    async def process_batch(
        self,
        queries: list[str],
        retrieval_only: bool = False,
    ) -> list[GeneratedResponse | list[RetrievalResult]]:
        """Process ``queries`` and return results in-order.

        A failure on any single query yields a fallback response (for
        generation mode) or an empty list (for retrieval-only mode) at
        that position; the batch itself never raises.

        Args:
            queries: List of raw query strings.
            retrieval_only: If True, skip generation and return retrieval
                results for each query.

        Returns:
            A list of ``GeneratedResponse`` or ``list[RetrievalResult]``,
            one entry per input query.
        """
        if not retrieval_only and self._generation_pipeline is None:
            raise ValueError(
                "generation_pipeline is required unless retrieval_only=True"
            )

        results: list[GeneratedResponse | list[RetrievalResult]] = []
        if not queries:
            return results

        logger.info(
            "batch_processing_start",
            count=len(queries),
            retrieval_only=retrieval_only,
        )

        for idx, query in enumerate(queries):
            try:
                retrieval = self._retriever.retrieve(RetrievalRequest(query=query))
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "batch_retrieve_failed",
                    index=idx,
                    query=query[:60],
                    error=str(exc),
                )
                if retrieval_only:
                    results.append([])
                else:
                    results.append(self._error_response(query, str(exc)))
                continue

            if retrieval_only:
                results.append(retrieval)
            else:
                try:
                    response = await self._generation_pipeline.generate_answer(
                        query=query,
                        retrieval_results=retrieval,
                    )
                    results.append(response)
                except Exception as exc:  # noqa: BLE001
                    logger.warning(
                        "batch_generation_failed",
                        index=idx,
                        query=query[:60],
                        error=str(exc),
                    )
                    results.append(self._error_response(query, str(exc)))

            if (idx + 1) % self._batch_size == 0:
                logger.info(
                    "batch_progress",
                    processed=idx + 1,
                    total=len(queries),
                )

        logger.info(
            "batch_processing_complete",
            count=len(queries),
            success=sum(1 for r in results if r),
        )
        return results

    @staticmethod
    def _error_response(query: str, error: str) -> GeneratedResponse:
        from mrag.generation.models import GeneratedResponse  # noqa: F811

        return GeneratedResponse(
            query=query,
            answer=f"Error processing query: {error}",
            confidence_score=0.0,
            is_fallback=True,
            sources=[],
            metrics=RequestMetrics(),
        )
