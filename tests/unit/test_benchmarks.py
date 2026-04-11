"""Unit tests for benchmark latency computations."""

from __future__ import annotations

import pytest

from mrag.evaluation.benchmarks import run_benchmark


class FakeMetrics:
    def __init__(self, total_ms=1000.0, emb_ms=100.0, search_ms=200.0, llm_ms=500.0):
        self.total_time_ms = total_ms
        self.embedding_time_ms = emb_ms
        self.search_time_ms = search_ms
        self.llm_time_ms = llm_ms


class FakeResponse:
    def __init__(self, total_ms=1000.0):
        self.metrics = FakeMetrics(total_ms)
        self.answer = "test answer"


class FakePipeline:
    def __init__(self, responses=None):
        self._responses = responses or [FakeResponse()]

    async def ask(self, query, **kwargs):
        idx = hash(query) % len(self._responses)
        return self._responses[idx]


class TestRunBenchmark:
    @pytest.mark.asyncio
    async def test_basic_benchmark(self):
        pipeline = FakePipeline(
            [
                FakeResponse(500.0),
                FakeResponse(1000.0),
                FakeResponse(1500.0),
            ]
        )
        result = await run_benchmark(pipeline, ["q1", "q2", "q3"])
        assert result.num_queries == 3
        assert result.p50_ms > 0
        assert result.qps > 0

    @pytest.mark.asyncio
    async def test_empty_queries(self):
        pipeline = FakePipeline()
        result = await run_benchmark(pipeline, [])
        assert result.num_queries == 0
        assert result.p50_ms == 0.0

    @pytest.mark.asyncio
    async def test_single_query(self):
        pipeline = FakePipeline([FakeResponse(2000.0)])
        result = await run_benchmark(pipeline, ["q1"])
        assert result.num_queries == 1
        assert result.p50_ms == 2000.0
