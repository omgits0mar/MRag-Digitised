"""Per-request timing and aggregate percentile metrics.

Uses ``time.perf_counter_ns()`` for sub-microsecond resolution timers
and ``numpy.percentile`` for p50/p95/p99 latency summaries.
"""

from __future__ import annotations

import time
from typing import Any

import numpy as np
import structlog

from mrag.cache.models import RequestMetrics

logger = structlog.get_logger(__name__)

# Numeric fields from RequestMetrics that we compute percentiles over.
_METRIC_FIELDS: tuple[str, ...] = (
    "preprocessing_time_ms",
    "embedding_time_ms",
    "search_time_ms",
    "llm_time_ms",
    "total_time_ms",
)


class MetricsCollector:
    """Accumulate per-request metrics and compute aggregate statistics.

    Thread safety is not required (single-process async event loop per
    Phase 2 scope; see research.md R6).
    """

    def __init__(self) -> None:
        self._timers: dict[str, int] = {}
        self._records: list[RequestMetrics] = []

    # ---------------------------------------------------------------- timers

    def start_timer(self, label: str) -> None:
        """Record the start of a named timer using ``perf_counter_ns``."""
        self._timers[label] = time.perf_counter_ns()

    def stop_timer(self, label: str) -> float:
        """Stop a named timer and return elapsed milliseconds.

        Raises:
            KeyError: If ``start_timer`` was not called for ``label``.
        """
        start = self._timers.pop(label)
        elapsed_ns = time.perf_counter_ns() - start
        return elapsed_ns / 1_000_000  # ns → ms

    # --------------------------------------------------------------- records

    def record(self, metrics: RequestMetrics) -> None:
        """Append a completed request's metrics to the accumulator."""
        self._records.append(metrics)
        logger.debug(
            "metrics_recorded",
            total_time_ms=round(metrics.total_time_ms, 1),
            cache_hit=metrics.cache_hit,
        )

    # --------------------------------------------------------------- summary

    def get_summary(self) -> dict[str, dict[str, float]]:
        """Compute p50, p95, p99 for each numeric metric field.

        Returns:
            A dict keyed by metric field name, each containing
            ``{"p50": ..., "p95": ..., "p99": ...}``. Also includes
            ``"cache_hit_rate"`` as a top-level float.
        """
        if not self._records:
            return {
                field: {"p50": 0.0, "p95": 0.0, "p99": 0.0} for field in _METRIC_FIELDS
            } | {
                "cache_hit_rate": 0.0,
            }

        summary: dict[str, Any] = {}
        for field in _METRIC_FIELDS:
            values = [getattr(r, field) for r in self._records]
            arr = np.array(values, dtype=np.float64)
            summary[field] = {
                "p50": float(np.percentile(arr, 50)),
                "p95": float(np.percentile(arr, 95)),
                "p99": float(np.percentile(arr, 99)),
            }

        hits = sum(1 for r in self._records if r.cache_hit)
        summary["cache_hit_rate"] = hits / len(self._records)

        return summary

    # ------------------------------------------------------------------ util

    def reset(self) -> None:
        """Clear all accumulated metrics and timers."""
        self._records.clear()
        self._timers.clear()
        logger.debug("metrics_reset")

    @property
    def request_count(self) -> int:
        """Total number of recorded requests."""
        return len(self._records)
