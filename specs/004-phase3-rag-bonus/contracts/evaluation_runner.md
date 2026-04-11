# Contract: Evaluation Runner

**Module**: `src/mrag/evaluation/`

## Dataset Loader (`dataset_loader.py`)

```python
from mrag.evaluation.models import EvaluationDataset

def load_evaluation_dataset(path: str) -> EvaluationDataset:
    """Load the held-out evaluation dataset from disk.

    Reads the Phase 1 eval split (default: data/processed/eval.jsonl)
    which contains ProcessedDocument JSONL records produced by the
    deterministic 90/10 split of Natural-Questions-Filtered.csv.

    For each ProcessedDocument:
        - query_id  ← doc.doc_id
        - question  ← doc.question
        - relevant_chunk_ids ← {chunk.chunk_id for chunk in doc.chunks}
        - reference_answer ← doc.answer_short (nullable; used for BLEU/ROUGE)

    Validates each record and skips malformed rows with a warning.

    Args:
        path: Filesystem path to the JSONL file
              (default: Settings.eval_heldout_path = "data/processed/eval.jsonl").

    Returns:
        EvaluationDataset with validated EvaluationQuery entries.

    Raises:
        FileNotFoundError: If path does not exist.
        EvaluationError: If no valid queries after loading.
    """
```

## Retrieval Metrics (`retrieval_metrics.py`)

```python
def precision_at_k(predicted: list[str], relevant: set[str], k: int) -> float:
    """Precision@K: fraction of the top-K predicted IDs that are relevant.

    Args:
        predicted: Ranked list of predicted chunk IDs (best first).
        relevant: Set of ground-truth relevant chunk IDs.
        k: Cutoff rank.

    Returns:
        Float in [0, 1]. Returns 0.0 if k <= 0 or predicted is empty.
    """

def recall_at_k(predicted: list[str], relevant: set[str], k: int) -> float:
    """Recall@K: fraction of relevant IDs found in the top-K predictions.

    Args:
        predicted: Ranked list of predicted chunk IDs (best first).
        relevant: Set of ground-truth relevant chunk IDs.
        k: Cutoff rank.

    Returns:
        Float in [0, 1]. Returns 0.0 if relevant is empty.
    """

def reciprocal_rank(predicted: list[str], relevant: set[str]) -> float:
    """Reciprocal rank for a single query: 1/rank of first relevant hit.

    Returns:
        Float in [0, 1]. Returns 0.0 if no relevant item found.
    """

def mean_reciprocal_rank(
    rankings: list[list[str]],
    relevants: list[set[str]],
) -> float:
    """Mean reciprocal rank over multiple queries.

    Args:
        rankings: List of ranked prediction lists, one per query.
        relevants: List of relevant ID sets, one per query.

    Returns:
        Float in [0, 1].
    """

def average_precision(predicted: list[str], relevant: set[str]) -> float:
    """Average precision for a single query.

    Returns:
        Float in [0, 1]. Returns 0.0 if relevant is empty.
    """

def mean_average_precision(
    rankings: list[list[str]],
    relevants: list[set[str]],
) -> float:
    """Mean average precision over multiple queries.

    Returns:
        Float in [0, 1].
    """
```

## Response Metrics (`response_metrics.py`)

```python
def compute_bleu(
    predictions: list[str],
    references: list[str],
) -> float:
    """Corpus-level BLEU score via sacrebleu.

    Args:
        predictions: Generated answer texts.
        references: Ground-truth reference answer texts.

    Returns:
        Float in [0, 1] (sacrebleu's 0–100 scale normalized).
    """

def compute_rouge(
    predictions: list[str],
    references: list[str],
) -> dict[str, float]:
    """ROUGE-1, ROUGE-2, ROUGE-L fmeasure scores.

    Uses Google's rouge-score library with stemming enabled.

    Args:
        predictions: Generated answer texts.
        references: Ground-truth reference answer texts.

    Returns:
        {"rouge_1": float, "rouge_2": float, "rouge_l": float}
        Each in [0, 1], averaged over all pairs.
    """
```

## Benchmarks (`benchmarks.py`)

```python
from mrag.evaluation.models import BenchmarkResult
from mrag.pipeline import MRAGPipeline

async def run_benchmark(
    pipeline: MRAGPipeline,
    queries: list[str],
) -> BenchmarkResult:
    """Run latency/throughput benchmark on the given queries.

    Processes each query through pipeline.ask() sequentially,
    collecting per-request timing from RequestMetrics.

    Computes p50, p95, p99 for total_time_ms and per-stage,
    plus queries-per-second throughput.

    Args:
        pipeline: Configured MRAGPipeline instance.
        queries: List of query strings for the benchmark.

    Returns:
        BenchmarkResult with latency percentiles and throughput.
    """
```

## Baseline Comparison (`baseline.py`)

```python
from mrag.evaluation.models import EvaluationReport, BaselineComparison

def load_baseline(path: str) -> dict | None:
    """Load baseline metrics from a JSON file.

    Returns:
        Parsed JSON dict, or None if file does not exist.
    """

def compare_to_baseline(
    report: EvaluationReport,
    baseline: dict,
    threshold_pct: float = 0.05,
) -> BaselineComparison:
    """Compare current evaluation metrics against a baseline.

    Flags any metric where (baseline - current) / baseline > threshold_pct.

    Args:
        report: The current evaluation report.
        baseline: The baseline metrics dict (from load_baseline).
        threshold_pct: Regression threshold (default 5%).

    Returns:
        BaselineComparison with per-metric deltas and has_regressions flag.
    """

def save_baseline(report: EvaluationReport, path: str) -> None:
    """Save current metrics as the new baseline JSON file.

    Overwrites any existing file at path.
    """
```

## Report Generator (`report_generator.py`)

```python
from mrag.evaluation.models import EvaluationReport

def generate_report(
    report: EvaluationReport,
    output_dir: str,
    template_path: str = "prompts/templates/report.html.j2",
) -> str:
    """Generate a self-contained HTML evaluation report.

    Produces charts via matplotlib:
        1. Precision vs K (line chart)
        2. Latency distribution (histogram)
        3. Score histogram (ROUGE-L distribution, if per-query data available)

    Charts are base64-encoded PNG embedded in the HTML.
    Template is loaded from the Jinja2 template path.

    Args:
        report: Complete EvaluationReport with all metrics.
        output_dir: Directory to write the HTML file.
        template_path: Path to the Jinja2 HTML template.

    Returns:
        Full filesystem path to the generated HTML file.
    """
```

## Evaluation Runner (`runner.py`)

```python
from mrag.evaluation.models import EvaluationDataset, EvaluationReport
from mrag.pipeline import MRAGPipeline

class EvaluationRunner:
    """Orchestrates the full evaluation suite.

    Can be invoked from:
        - The API endpoint (POST /evaluate)
        - A standalone script (no API server needed — FR-022)

    Args:
        pipeline: MRAGPipeline instance for running queries.
        settings: Optional Settings override for eval paths and thresholds.
    """

    def __init__(
        self,
        pipeline: MRAGPipeline,
        settings: Settings | None = None,
    ) -> None: ...

    async def run_full_evaluation(
        self,
        dataset: EvaluationDataset | None = None,
        dataset_path: str | None = None,
        k_values: list[int] | None = None,
        generate_report: bool = True,
        compare_baseline: bool = True,
    ) -> EvaluationReport:
        """Execute the complete evaluation pipeline.

        Flow:
            1. Load dataset (from param or default path).
            2. For each query:
                a. Run pipeline.ask() to get predictions.
                b. Collect predicted chunk IDs from sources.
                c. Collect generated answer text.
            3. Compute retrieval metrics (precision@K, recall@K, MRR, MAP).
            4. Compute response quality (BLEU, ROUGE) for queries with references.
            5. Run latency benchmark on dataset queries.
            6. Load baseline and compare (if compare_baseline=True).
            7. Generate HTML report (if generate_report=True).
            8. Return assembled EvaluationReport.

        Args:
            dataset: Pre-loaded dataset; if None, loads from dataset_path.
            dataset_path: Path override; falls back to settings.eval_heldout_path.
            k_values: K values for retrieval metrics; falls back to settings.eval_k_values.
            generate_report: Whether to produce the HTML artifact.
            compare_baseline: Whether to compare against saved baseline.

        Returns:
            EvaluationReport with all metrics, optional baseline comparison,
            and optional report file path.

        Raises:
            EvaluationError: If dataset loading fails or no queries are valid.
        """
```
