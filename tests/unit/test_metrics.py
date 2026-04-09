"""Unit tests for mrag.cache.metrics.MetricsCollector."""

from __future__ import annotations

import time

from mrag.cache.metrics import MetricsCollector
from mrag.cache.models import RequestMetrics


class TestMetricsCollector:
    def test_start_stop_timer_returns_ms(self) -> None:
        mc = MetricsCollector()
        mc.start_timer("test")
        time.sleep(0.01)  # 10 ms
        elapsed = mc.stop_timer("test")
        # Should be roughly 10 ms ± a few ms of overhead.
        assert elapsed >= 5.0
        assert elapsed < 200.0

    def test_stop_timer_without_start_raises(self) -> None:
        mc = MetricsCollector()
        try:
            mc.stop_timer("missing")
            raise AssertionError("Expected KeyError")
        except KeyError:
            pass

    def test_record_and_request_count(self) -> None:
        mc = MetricsCollector()
        assert mc.request_count == 0
        mc.record(RequestMetrics(total_time_ms=100.0))
        mc.record(RequestMetrics(total_time_ms=200.0))
        assert mc.request_count == 2

    def test_get_summary_computes_percentiles(self) -> None:
        mc = MetricsCollector()
        for i in range(1, 11):
            mc.record(
                RequestMetrics(
                    preprocessing_time_ms=float(i),
                    embedding_time_ms=float(i),
                    search_time_ms=float(i),
                    llm_time_ms=float(i),
                    total_time_ms=float(i * 10),
                )
            )
        summary = mc.get_summary()
        # total_time_ms: values are 10, 20, ..., 100
        total = summary["total_time_ms"]
        assert total["p50"] > 0
        assert total["p95"] >= total["p50"]
        assert total["p99"] >= total["p95"]

    def test_cache_hit_rate(self) -> None:
        mc = MetricsCollector()
        mc.record(RequestMetrics(cache_hit=True))
        mc.record(RequestMetrics(cache_hit=True))
        mc.record(RequestMetrics(cache_hit=False))
        mc.record(RequestMetrics(cache_hit=False))
        summary = mc.get_summary()
        assert summary["cache_hit_rate"] == 0.5

    def test_empty_summary_returns_zeros(self) -> None:
        mc = MetricsCollector()
        summary = mc.get_summary()
        assert summary["total_time_ms"]["p50"] == 0.0
        assert summary["cache_hit_rate"] == 0.0

    def test_reset_clears_everything(self) -> None:
        mc = MetricsCollector()
        mc.record(RequestMetrics(total_time_ms=50.0))
        mc.start_timer("x")
        mc.reset()
        assert mc.request_count == 0
        # Timer should be gone too.
        try:
            mc.stop_timer("x")
            raise AssertionError("Expected KeyError")
        except KeyError:
            pass
