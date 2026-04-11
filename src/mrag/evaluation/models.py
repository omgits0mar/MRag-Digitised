"""Pydantic models for the evaluation framework.

Defines data structures for evaluation queries, metrics, benchmarks,
baseline comparison, and the aggregate evaluation report.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class EvaluationQuery(BaseModel):
    """A single query in the held-out evaluation dataset.

    Derived from Phase 1 ``ProcessedDocument`` records.

    Attributes:
        query_id: Unique identifier (maps to ProcessedDocument.doc_id).
        question: The question text.
        relevant_chunk_ids: Ground-truth relevant chunk IDs.
        reference_answer: Ground-truth short answer (for BLEU/ROUGE).
    """

    query_id: str
    question: str = Field(min_length=1)
    relevant_chunk_ids: set[str]
    reference_answer: str | None = None


class EvaluationDataset(BaseModel):
    """Container for the held-out evaluation set."""

    name: str
    queries: list[EvaluationQuery] = Field(min_length=1)
    created_at: str  # ISO 8601


class RetrievalMetrics(BaseModel):
    """Computed retrieval quality metrics for a run."""

    precision_at_k: dict[int, float]
    recall_at_k: dict[int, float]
    mrr: float = Field(ge=0.0, le=1.0)
    map: float = Field(ge=0.0, le=1.0)
    num_queries: int = Field(ge=1)


class ResponseQualityMetrics(BaseModel):
    """Computed response quality scores for a run."""

    bleu: float = Field(ge=0.0, le=1.0)
    rouge_1: float = Field(ge=0.0, le=1.0)
    rouge_2: float = Field(ge=0.0, le=1.0)
    rouge_l: float = Field(ge=0.0, le=1.0)
    num_pairs: int = Field(ge=1)


class BenchmarkResult(BaseModel):
    """Latency and throughput benchmarks for a run."""

    p50_ms: float = Field(ge=0.0)
    p95_ms: float = Field(ge=0.0)
    p99_ms: float = Field(ge=0.0)
    qps: float = Field(ge=0.0)
    num_queries: int = Field(ge=0)
    per_stage: dict[str, dict[str, float]] = Field(default_factory=dict)


class RegressionFlag(BaseModel):
    """A single metric regression entry for baseline comparison."""

    metric: str
    baseline_value: float
    current_value: float
    delta_pct: float
    status: str  # "PASS" | "REGRESS"


class BaselineComparison(BaseModel):
    """Result of comparing current metrics against a prior baseline."""

    baseline_generated_at: str  # ISO 8601
    threshold_pct: float = Field(ge=0.0, le=1.0)
    deltas: list[RegressionFlag]
    has_regressions: bool


class EvaluationReport(BaseModel):
    """Top-level aggregation combining all evaluation results."""

    generated_at: str  # ISO 8601
    mrag_version: str
    dataset_name: str
    retrieval: RetrievalMetrics
    response_quality: ResponseQualityMetrics
    benchmark: BenchmarkResult
    baseline_comparison: BaselineComparison | None = None
    report_path: str | None = None
