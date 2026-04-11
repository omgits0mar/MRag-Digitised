"""Unit tests for baseline comparison."""

from __future__ import annotations

import json
import os
import tempfile

from mrag.evaluation.baseline import compare_to_baseline, load_baseline, save_baseline
from mrag.evaluation.models import (
    BaselineComparison,
    BenchmarkResult,
    EvaluationReport,
    ResponseQualityMetrics,
    RetrievalMetrics,
)


def _make_report(
    precision=0.5,
    recall=0.6,
    mrr=0.55,
    map_val=0.48,
    bleu=0.32,
    rouge_l=0.47,
    p50=1200.0,
    p95=2800.0,
    qps=0.83,
) -> EvaluationReport:
    return EvaluationReport(
        generated_at="2026-04-11T00:00:00Z",
        mrag_version="0.1.0",
        dataset_name="test",
        retrieval=RetrievalMetrics(
            precision_at_k={1: precision, 5: precision * 0.8},
            recall_at_k={5: recall, 10: recall * 1.1},
            mrr=mrr,
            map=map_val,
            num_queries=10,
        ),
        response_quality=ResponseQualityMetrics(
            bleu=bleu,
            rouge_1=0.51,
            rouge_2=0.28,
            rouge_l=rouge_l,
            num_pairs=10,
        ),
        benchmark=BenchmarkResult(
            p50_ms=p50,
            p95_ms=p95,
            p99_ms=3400.0,
            qps=qps,
            num_queries=10,
        ),
    )


class TestLoadBaseline:
    def test_missing_file_returns_none(self):
        assert load_baseline("/nonexistent/path.json") is None

    def test_existing_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"retrieval": {"mrr": 0.5}}, f)
            f.flush()
            result = load_baseline(f.name)
        os.unlink(f.name)
        assert result is not None
        assert result["retrieval"]["mrr"] == 0.5


class TestCompareToBaseline:
    def test_no_regressions(self):
        report = _make_report(mrr=0.6, map_val=0.5)
        baseline = {
            "generated_at": "2026-04-10T00:00:00Z",
            "retrieval": {"mrr": 0.55, "map": 0.48},
            "response": {"bleu": 0.3, "rouge_1": 0.5, "rouge_2": 0.27, "rouge_l": 0.45},
            "benchmark": {"p50_ms": 1200, "p95_ms": 2800, "p99_ms": 3400, "qps": 0.83},
        }
        comparison = compare_to_baseline(report, baseline, threshold_pct=0.05)
        assert isinstance(comparison, BaselineComparison)
        # All metrics improved or stayed the same, so no regressions
        assert not comparison.has_regressions

    def test_regression_detected(self):
        report = _make_report(mrr=0.3, map_val=0.2)  # major drop
        baseline = {
            "generated_at": "2026-04-10T00:00:00Z",
            "retrieval": {"mrr": 0.6, "map": 0.5},
            "response": {
                "bleu": 0.32,
                "rouge_1": 0.51,
                "rouge_2": 0.28,
                "rouge_l": 0.47,
            },
            "benchmark": {"p50_ms": 1200, "p95_ms": 2800, "p99_ms": 3400, "qps": 0.83},
        }
        comparison = compare_to_baseline(report, baseline, threshold_pct=0.05)
        assert comparison.has_regressions
        regressed = [d for d in comparison.deltas if d.status == "REGRESS"]
        assert len(regressed) > 0


class TestSaveBaseline:
    def test_save_and_reload(self):
        report = _make_report()
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "baseline.json")
            save_baseline(report, path)
            loaded = load_baseline(path)
            assert loaded is not None
            assert loaded["response"]["bleu"] == 0.32
