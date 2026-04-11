"""Unit tests for report generator."""

from __future__ import annotations

import os
import tempfile

from mrag.evaluation.models import (
    BenchmarkResult,
    EvaluationReport,
    ResponseQualityMetrics,
    RetrievalMetrics,
)
from mrag.evaluation.report_generator import generate_report


def _make_report() -> EvaluationReport:
    return EvaluationReport(
        generated_at="2026-04-11T12:00:00Z",
        mrag_version="0.1.0",
        dataset_name="test",
        retrieval=RetrievalMetrics(
            precision_at_k={1: 0.6, 3: 0.5, 5: 0.4},
            recall_at_k={5: 0.7, 10: 0.8},
            mrr=0.55,
            map=0.48,
            num_queries=200,
        ),
        response_quality=ResponseQualityMetrics(
            bleu=0.32,
            rouge_1=0.51,
            rouge_2=0.28,
            rouge_l=0.47,
            num_pairs=200,
        ),
        benchmark=BenchmarkResult(
            p50_ms=1200.0,
            p95_ms=2800.0,
            p99_ms=3400.0,
            qps=0.83,
            num_queries=200,
        ),
    )


class TestGenerateReport:
    def test_html_file_created(self):
        report = _make_report()
        with tempfile.TemporaryDirectory() as tmpdir:
            path = generate_report(report, tmpdir)
            assert os.path.exists(path)
            assert path.endswith(".html")

    def test_html_contains_key_sections(self):
        report = _make_report()
        with tempfile.TemporaryDirectory() as tmpdir:
            path = generate_report(report, tmpdir)
            with open(path, encoding="utf-8") as f:
                html = f.read()

        assert "MRAG Evaluation Report" in html
        assert "Retrieval" in html
        assert "BLEU" in html
        assert "ROUGE" in html
        assert "Latency" in html
        assert "base64" in html  # charts embedded

    def test_html_self_contained(self):
        report = _make_report()
        with tempfile.TemporaryDirectory() as tmpdir:
            path = generate_report(report, tmpdir)
            with open(path, encoding="utf-8") as f:
                html = f.read()

        # Should not reference external files
        assert 'src="http' not in html
        assert 'href="http' not in html
