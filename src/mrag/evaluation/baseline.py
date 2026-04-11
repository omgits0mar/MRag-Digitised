"""Baseline metric comparison and regression flagging.

Loads/saves a JSON baseline file and compares current metrics against it
using a relative regression threshold.
"""

from __future__ import annotations

import json
import os

import structlog

from mrag.evaluation.models import (
    BaselineComparison,
    EvaluationReport,
    RegressionFlag,
)

logger = structlog.get_logger(__name__)


def load_baseline(path: str) -> dict | None:
    """Load baseline metrics from a JSON file.

    Returns:
        Parsed JSON dict, or None if file does not exist.
    """
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def compare_to_baseline(
    report: EvaluationReport,
    baseline: dict,
    threshold_pct: float = 0.05,
) -> BaselineComparison:
    """Compare current evaluation metrics against a baseline.

    Flags any metric where (baseline - current) / baseline > threshold_pct.
    """
    flat_current = _flatten_metrics(report)
    flat_baseline = _flatten_baseline(baseline)

    deltas: list[RegressionFlag] = []

    for metric_name, baseline_val in flat_baseline.items():
        current_val = flat_current.get(metric_name, 0.0)
        if baseline_val == 0:
            delta_pct = 0.0
        else:
            delta_pct = (current_val - baseline_val) / baseline_val

        is_regression = (
            (baseline_val - current_val) / baseline_val > threshold_pct
            if baseline_val > 0
            else False
        )

        deltas.append(
            RegressionFlag(
                metric=metric_name,
                baseline_value=baseline_val,
                current_value=current_val,
                delta_pct=delta_pct,
                status="REGRESS" if is_regression else "PASS",
            )
        )

    has_regressions = any(d.status == "REGRESS" for d in deltas)

    return BaselineComparison(
        baseline_generated_at=baseline.get("generated_at", "unknown"),
        threshold_pct=threshold_pct,
        deltas=deltas,
        has_regressions=has_regressions,
    )


def save_baseline(report: EvaluationReport, path: str) -> None:
    """Save current metrics as the new baseline JSON file."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    data = {
        "generated_at": report.generated_at,
        "mrag_version": report.mrag_version,
        "retrieval": {
            f"precision_at_{k}": v for k, v in report.retrieval.precision_at_k.items()
        }
        | {f"recall_at_{k}": v for k, v in report.retrieval.recall_at_k.items()}
        | {"mrr": report.retrieval.mrr, "map": report.retrieval.map},
        "response": {
            "bleu": report.response_quality.bleu,
            "rouge_1": report.response_quality.rouge_1,
            "rouge_2": report.response_quality.rouge_2,
            "rouge_l": report.response_quality.rouge_l,
        },
        "benchmark": {
            "p50_ms": report.benchmark.p50_ms,
            "p95_ms": report.benchmark.p95_ms,
            "p99_ms": report.benchmark.p99_ms,
            "qps": report.benchmark.qps,
        },
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    logger.info("baseline_saved", path=path)


def _flatten_metrics(report: EvaluationReport) -> dict[str, float]:
    """Flatten an EvaluationReport into metric_name -> value."""
    flat: dict[str, float] = {}
    for k, v in report.retrieval.precision_at_k.items():
        flat[f"precision_at_{k}"] = v
    for k, v in report.retrieval.recall_at_k.items():
        flat[f"recall_at_{k}"] = v
    flat["mrr"] = report.retrieval.mrr
    flat["map"] = report.retrieval.map
    flat["bleu"] = report.response_quality.bleu
    flat["rouge_1"] = report.response_quality.rouge_1
    flat["rouge_2"] = report.response_quality.rouge_2
    flat["rouge_l"] = report.response_quality.rouge_l
    flat["p50_ms"] = report.benchmark.p50_ms
    flat["p95_ms"] = report.benchmark.p95_ms
    flat["p99_ms"] = report.benchmark.p99_ms
    flat["qps"] = report.benchmark.qps
    return flat


def _flatten_baseline(baseline: dict) -> dict[str, float]:
    """Flatten a baseline JSON dict into metric_name -> value."""
    flat: dict[str, float] = {}
    for section_key in ("retrieval", "response", "benchmark"):
        section = baseline.get(section_key, {})
        for k, v in section.items():
            flat[k] = float(v)
    return flat
