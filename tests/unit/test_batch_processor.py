"""Unit tests for mrag.cache.batch_processor.BatchProcessor."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from mrag.cache.batch_processor import BatchProcessor
from mrag.cache.models import RequestMetrics
from mrag.generation.models import GeneratedResponse
from mrag.retrieval.models import RetrievalResult


def _mk_result(i: int) -> RetrievalResult:
    return RetrievalResult(
        chunk_id=f"c{i}",
        doc_id=f"d{i}",
        chunk_text=f"text{i}",
        relevance_score=0.8,
        cosine_similarity=0.8,
        question=f"q{i}",
        answer_short=None,
        answer_long=f"a{i}",
        question_type="factoid",
        domain="science",
        difficulty="easy",
        has_short_answer=False,
    )


def _mk_response(query: str) -> GeneratedResponse:
    return GeneratedResponse(
        query=query,
        answer=f"ans: {query}",
        confidence_score=0.9,
        is_fallback=False,
        sources=[],
        metrics=RequestMetrics(),
    )


@pytest.mark.asyncio
class TestBatchProcessor:
    async def test_empty_list_returns_empty(self) -> None:
        bp = BatchProcessor(retriever=MagicMock(), generation_pipeline=AsyncMock())
        assert await bp.process_batch([]) == []

    async def test_retrieval_only_mode(self) -> None:
        retriever = MagicMock()
        retriever.retrieve.side_effect = [
            [_mk_result(1), _mk_result(2)],
            [_mk_result(3)],
        ]
        bp = BatchProcessor(retriever=retriever, generation_pipeline=None)
        results = await bp.process_batch(["q1", "q2"], retrieval_only=True)
        assert len(results) == 2
        assert len(results[0]) == 2
        assert len(results[1]) == 1

    async def test_full_pipeline_mode(self) -> None:
        retriever = MagicMock()
        retriever.retrieve.return_value = [_mk_result(1)]
        gp = AsyncMock()
        gp.generate_answer = AsyncMock(
            side_effect=lambda query, **_: _mk_response(query)
        )
        bp = BatchProcessor(retriever=retriever, generation_pipeline=gp)

        results = await bp.process_batch(["q1", "q2", "q3"])
        assert len(results) == 3
        for r, q in zip(results, ["q1", "q2", "q3"], strict=True):
            assert isinstance(r, GeneratedResponse)
            assert r.query == q

    async def test_single_query_failure_isolated(self) -> None:
        retriever = MagicMock()
        retriever.retrieve.side_effect = [
            [_mk_result(1)],
            RuntimeError("index missing"),
            [_mk_result(2)],
        ]
        gp = AsyncMock()
        gp.generate_answer = AsyncMock(
            side_effect=lambda query, **_: _mk_response(query)
        )
        bp = BatchProcessor(retriever=retriever, generation_pipeline=gp)

        results = await bp.process_batch(["ok1", "bad", "ok2"])
        assert len(results) == 3
        assert isinstance(results[0], GeneratedResponse)
        assert results[0].is_fallback is False
        assert isinstance(results[1], GeneratedResponse)
        assert results[1].is_fallback is True
        assert "Error" in results[1].answer
        assert results[2].is_fallback is False

    async def test_generation_failure_isolated(self) -> None:
        retriever = MagicMock()
        retriever.retrieve.return_value = [_mk_result(1)]
        gp = AsyncMock()
        gp.generate_answer = AsyncMock(side_effect=RuntimeError("llm down"))
        bp = BatchProcessor(retriever=retriever, generation_pipeline=gp)
        results = await bp.process_batch(["q1"])
        assert results[0].is_fallback is True
        assert "llm down" in results[0].answer

    async def test_no_generation_pipeline_requires_retrieval_only(self) -> None:
        bp = BatchProcessor(retriever=MagicMock(), generation_pipeline=None)
        with pytest.raises(ValueError):
            await bp.process_batch(["q"])

    async def test_invalid_batch_size(self) -> None:
        with pytest.raises(ValueError):
            BatchProcessor(retriever=MagicMock(), batch_size=0)
