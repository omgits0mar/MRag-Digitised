"""Latency and throughput benchmarks for evaluation."""

from __future__ import annotations

import time

import numpy as np
import structlog

from mrag.evaluation.models import BenchmarkResult

logger = structlog.get_logger(__name__)


async def run_benchmark(
    pipeline,
    queries: list[str],
) -> BenchmarkResult:
    """Run latency/throughput benchmark on the given queries.

    Processes each query through pipeline.ask() sequentially,
    collecting per-request timing from RequestMetrics.

    Args:
        pipeline: Configured MRAGPipeline instance.
        queries: List of query strings for the benchmark.

    Returns:
        BenchmarkResult with latency percentiles and throughput.
    """
    if not queries:
        return BenchmarkResult(
            p50_ms=0.0,
            p95_ms=0.0,
            p99_ms=0.0,
            qps=0.0,
            num_queries=0,
        )

    total_times: list[float] = []
    per_stage_times: dict[str, list[float]] = {
        "embedding_time_ms": [],
        "search_time_ms": [],
        "llm_time_ms": [],
    }

    start = time.perf_counter()

    for query in queries:
        response = await pipeline.ask(query=query)
        m = response.metrics
        total_times.append(m.total_time_ms)
        if m.embedding_time_ms:
            per_stage_times["embedding_time_ms"].append(m.embedding_time_ms)
        if m.search_time_ms:
            per_stage_times["search_time_ms"].append(m.search_time_ms)
        if m.llm_time_ms:
            per_stage_times["llm_time_ms"].append(m.llm_time_ms)

    wall_seconds = time.perf_counter() - start
    qps = len(queries) / wall_seconds if wall_seconds > 0 else 0.0

    total_arr = np.array(total_times, dtype=np.float64)

    def _percentiles(arr: np.ndarray) -> dict[str, float]:
        if len(arr) == 0:
            return {"p50": 0.0, "p95": 0.0, "p99": 0.0}
        return {
            "p50": float(np.percentile(arr, 50)),
            "p95": float(np.percentile(arr, 95)),
            "p99": float(np.percentile(arr, 99)),
        }

    per_stage = {k: _percentiles(np.array(v)) for k, v in per_stage_times.items() if v}

    return BenchmarkResult(
        p50_ms=float(np.percentile(total_arr, 50)),
        p95_ms=float(np.percentile(total_arr, 95)),
        p99_ms=float(np.percentile(total_arr, 99)),
        qps=qps,
        num_queries=len(queries),
        per_stage=per_stage,
    )
