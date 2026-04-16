"""End-to-end integration test for Phase 2 RAG pipeline.

Tests the full MRAGPipeline orchestrator with mocked FAISS and LLM
layers, verifying cache hits, fallback, and metrics collection.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from mrag.cache.embedding_cache import EmbeddingCache
from mrag.cache.metrics import MetricsCollector
from mrag.cache.response_cache import ResponseCache
from mrag.generation.fallback import FallbackHandler
from mrag.generation.llm_client import BaseLLMClient
from mrag.generation.pipeline import GenerationPipeline
from mrag.generation.prompt_builder import PromptBuilder
from mrag.generation.validator import ResponseValidator
from mrag.pipeline import MRAGPipeline
from mrag.query.pipeline import QueryPipeline
from mrag.query.preprocessor import QueryPreprocessor
from mrag.retrieval.models import RetrievalResult
from mrag.retrieval.retriever import RetrieverService


def _chunk(text: str, score: float = 0.85) -> RetrievalResult:
    return RetrievalResult(
        chunk_id="c1",
        doc_id="d1",
        chunk_text=text,
        relevance_score=score,
        cosine_similarity=score,
        question="q",
        answer_short="a",
        answer_long=text,
        question_type="factoid",
        domain="science",
        difficulty="easy",
        has_short_answer=True,
    )


def _build_pipeline(
    with_cache: bool = False,
    with_metrics: bool = False,
    llm_response: str = "Photosynthesis converts light energy into chemical energy.",
) -> MRAGPipeline:
    """Build a pipeline with mocked retrieval and LLM."""
    # Query pipeline
    query_pipeline = QueryPipeline(
        preprocessor=QueryPreprocessor(),
        expander=None,
    )

    # Retriever — mocked
    retriever = MagicMock(spec=RetrieverService)
    retriever.retrieve.return_value = [
        _chunk(
            "Photosynthesis is a process by which plants convert light "
            "energy into chemical energy using chlorophyll.",
            0.92,
        ),
    ]

    # LLM — mocked
    llm = AsyncMock(spec=BaseLLMClient)
    llm.generate = AsyncMock(return_value=llm_response)

    pb = PromptBuilder(templates_dir="prompts/templates")
    validator = ResponseValidator(confidence_threshold=0.3, alpha=0.6)
    fallback = FallbackHandler(pb)
    gen_pipeline = GenerationPipeline(llm, pb, validator, fallback)

    emb_cache = EmbeddingCache(max_size=100) if with_cache else None
    resp_cache = ResponseCache(max_size=100, default_ttl=3600) if with_cache else None
    metrics = MetricsCollector() if with_metrics else None

    return MRAGPipeline(
        query_pipeline=query_pipeline,
        retriever=retriever,
        generation_pipeline=gen_pipeline,
        embedding_cache=emb_cache,
        response_cache=resp_cache,
        metrics_collector=metrics,
    )


@pytest.mark.asyncio
class TestPhase2E2E:
    async def test_full_pipeline_returns_response(self) -> None:
        pipeline = _build_pipeline()
        response = await pipeline.ask("  What is photosynthesis?? ")

        assert response.query == "  What is photosynthesis?? "
        assert response.is_fallback is False
        assert len(response.answer) > 0
        assert response.confidence_score > 0.0
        assert len(response.sources) == 1
        assert response.metrics.total_time_ms > 0.0

    async def test_cache_hit_on_second_query(self) -> None:
        pipeline = _build_pipeline(with_cache=True)

        r1 = await pipeline.ask("what is photosynthesis")
        assert r1.metrics.cache_hit is False

        r2 = await pipeline.ask("what is photosynthesis")
        assert r2.metrics.cache_hit is True
        assert r2.metrics.cache_type == "response"
        assert r2.metrics.total_time_ms < r1.metrics.total_time_ms + 50  # faster

    async def test_fallback_on_low_confidence(self) -> None:
        # LLM returns something unrelated to the context, and retrieval scores
        # are low enough to push confidence below the 0.3 threshold.
        pipeline = _build_pipeline(
            llm_response="Quantum computing leverages qubits and superposition."
        )
        # Override the retriever to return low-relevance results.
        pipeline._retriever.retrieve.return_value = [
            _chunk(
                "Photosynthesis is a process by which plants convert light energy.",
                0.15,  # Low retrieval score
            ),
        ]
        response = await pipeline.ask("what is photosynthesis")
        assert response.is_fallback is True
        assert response.confidence_score < 0.3

    async def test_metrics_recorded(self) -> None:
        pipeline = _build_pipeline(with_metrics=True)
        await pipeline.ask("what is DNA")
        await pipeline.ask("what is RNA")

        mc = pipeline._metrics
        assert mc.request_count == 2
        summary = mc.get_summary()
        assert summary["total_time_ms"]["p50"] > 0.0
        assert summary["cache_hit_rate"] == 0.0  # No response cache
