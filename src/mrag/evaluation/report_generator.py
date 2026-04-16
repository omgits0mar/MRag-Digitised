"""HTML evaluation report generator.

Produces a self-contained HTML file with matplotlib charts embedded
as base64-encoded PNG images.
"""

from __future__ import annotations

import base64
import os
from datetime import datetime, timezone
from io import BytesIO

import matplotlib

matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt
import structlog
from jinja2 import Environment, FileSystemLoader

from mrag.evaluation.models import EvaluationReport

logger = structlog.get_logger(__name__)


def generate_report(
    report: EvaluationReport,
    output_dir: str,
    template_path: str = "prompts/templates",
) -> str:
    """Generate a self-contained HTML evaluation report.

    Args:
        report: Complete EvaluationReport with all metrics.
        output_dir: Directory to write the HTML file.
        template_path: Directory containing the Jinja2 template.

    Returns:
        Full filesystem path to the generated HTML file.
    """
    os.makedirs(output_dir, exist_ok=True)

    # Generate charts
    precision_png = _precision_vs_k_chart(report)
    latency_png = _latency_histogram(report)
    score_png = _score_histogram(report)

    # Render template
    template_file = os.path.join(template_path, "report.html.j2")
    if os.path.exists(template_file):
        env = Environment(loader=FileSystemLoader(template_path))
        template = env.get_template("report.html.j2")
    else:
        template = None

    if template:
        html = template.render(
            generated_at=report.generated_at,
            mrag_version=report.mrag_version,
            dataset_name=report.dataset_name,
            retrieval=report.retrieval,
            response_quality=report.response_quality,
            benchmark=report.benchmark,
            baseline_comparison=report.baseline_comparison,
            precision_vs_k_png=precision_png,
            latency_histogram_png=latency_png,
            score_histogram_png=score_png,
        )
    else:
        html = _default_html(report, precision_png, latency_png, score_png)

    # Write file
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"eval_{timestamp}.html"
    filepath = os.path.join(output_dir, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)

    logger.info("report_generated", path=filepath)
    return filepath


def _fig_to_base64(fig: plt.Figure) -> str:
    """Convert a matplotlib figure to a base64-encoded PNG string."""
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=100, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


def _precision_vs_k_chart(report: EvaluationReport) -> str:
    """Precision vs K line chart."""
    k_values = sorted(report.retrieval.precision_at_k.keys())
    precisions = [report.retrieval.precision_at_k[k] for k in k_values]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(k_values, precisions, "b-o", linewidth=2, markersize=8)
    ax.set_xlabel("K")
    ax.set_ylabel("Precision@K")
    ax.set_title("Precision vs K")
    ax.set_ylim(0, 1)
    ax.grid(True, alpha=0.3)
    return _fig_to_base64(fig)


def _latency_histogram(report: EvaluationReport) -> str:
    """Latency distribution placeholder (uses benchmark percentiles)."""
    fig, ax = plt.subplots(figsize=(8, 5))
    percentiles = ["p50", "p95", "p99"]
    values = [report.benchmark.p50_ms, report.benchmark.p95_ms, report.benchmark.p99_ms]
    ax.bar(percentiles, values, color=["#2196F3", "#FF9800", "#F44336"])
    ax.set_ylabel("Latency (ms)")
    ax.set_title("Latency Percentiles")
    ax.grid(True, alpha=0.3, axis="y")
    return _fig_to_base64(fig)


def _score_histogram(report: EvaluationReport) -> str:
    """Score distribution chart (ROUGE-L and BLEU)."""
    fig, ax = plt.subplots(figsize=(8, 5))
    metrics = ["BLEU", "ROUGE-1", "ROUGE-2", "ROUGE-L"]
    values = [
        report.response_quality.bleu,
        report.response_quality.rouge_1,
        report.response_quality.rouge_2,
        report.response_quality.rouge_l,
    ]
    colors = ["#4CAF50", "#2196F3", "#9C27B0", "#FF9800"]
    ax.bar(metrics, values, color=colors)
    ax.set_ylabel("Score")
    ax.set_title("Response Quality Metrics")
    ax.set_ylim(0, 1)
    ax.grid(True, alpha=0.3, axis="y")
    return _fig_to_base64(fig)


def _default_html(  # noqa: E501
    report: EvaluationReport,
    precision_png: str,
    latency_png: str,
    score_png: str,
) -> str:
    """Generate a default HTML report when no template is available."""
    baseline_section = ""
    if report.baseline_comparison:
        bc = report.baseline_comparison
        rows = ""
        for d in bc.deltas:
            color = "red" if d.status == "REGRESS" else "green"
            rows += f"<tr><td>{d.metric}</td><td>{d.baseline_value:.4f}</td><td>{d.current_value:.4f}</td><td style='color:{color}'>{d.status}</td></tr>"
        baseline_section = f"""
        <h2>Baseline Comparison</h2>
        <p>Threshold: {bc.threshold_pct * 100:.1f}% | Has Regressions: {'Yes' if bc.has_regressions else 'No'}</p>
        <table border='1' cellpadding='5' cellspacing='0'><tr><th>Metric</th><th>Baseline</th><th>Current</th><th>Status</th></tr>{rows}</table>
        """

    return f"""<!DOCTYPE html>
<html><head><title>MRAG Evaluation Report</title><style>
body {{ font-family: Arial, sans-serif; margin: 20px; }}
table {{ border-collapse: collapse; margin: 10px 0; }}
th, td {{ padding: 8px 12px; text-align: left; }}
th {{ background-color: #f0f0f0; }}
</style></head><body>
<h1>MRAG Evaluation Report</h1>
<p>Generated: {report.generated_at} | Version: {report.mrag_version} | Dataset: {report.dataset_name}</p>

<h2>Retrieval Metrics</h2>
<table border='1' cellpadding='5' cellspacing='0'>
<tr><th>Metric</th><th>Value</th></tr>
<tr><td>MRR</td><td>{report.retrieval.mrr:.4f}</td></tr>
<tr><td>MAP</td><td>{report.retrieval.map:.4f}</td></tr>
{"".join(f"<tr><td>Precision@{k}</td><td>{v:.4f}</td></tr>" for k, v in report.retrieval.precision_at_k.items())}
{"".join(f"<tr><td>Recall@{k}</td><td>{v:.4f}</td></tr>" for k, v in report.retrieval.recall_at_k.items())}
</table>
<img src='data:image/png;base64,{precision_png}' style='max-width:800px'>

<h2>Response Quality</h2>
<table border='1' cellpadding='5' cellspacing='0'>
<tr><th>Metric</th><th>Value</th></tr>
<tr><td>BLEU</td><td>{report.response_quality.bleu:.4f}</td></tr>
<tr><td>ROUGE-1</td><td>{report.response_quality.rouge_1:.4f}</td></tr>
<tr><td>ROUGE-2</td><td>{report.response_quality.rouge_2:.4f}</td></tr>
<tr><td>ROUGE-L</td><td>{report.response_quality.rouge_l:.4f}</td></tr>
</table>
<img src='data:image/png;base64,{score_png}' style='max-width:800px'>

<h2>Latency Benchmarks</h2>
<table border='1' cellpadding='5' cellspacing='0'>
<tr><th>Percentile</th><th>Latency (ms)</th></tr>
<tr><td>p50</td><td>{report.benchmark.p50_ms:.1f}</td></tr>
<tr><td>p95</td><td>{report.benchmark.p95_ms:.1f}</td></tr>
<tr><td>p99</td><td>{report.benchmark.p99_ms:.1f}</td></tr>
<tr><td>QPS</td><td>{report.benchmark.qps:.2f}</td></tr>
</table>
<img src='data:image/png;base64,{latency_png}' style='max-width:800px'>

{baseline_section}
</body></html>"""
