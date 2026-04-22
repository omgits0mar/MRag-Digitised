"""Pydantic request/response schemas for the MRAG API.

All API boundary validation happens here per Constitution Article VII.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Question endpoint
# ---------------------------------------------------------------------------


class QuestionRequest(BaseModel):
    """Incoming payload for POST /ask-question."""

    question: str = Field(min_length=1, max_length=2000)
    conversation_id: str | None = Field(default=None, max_length=64)
    expand: bool = True
    temperature: float = Field(default=0.1, ge=0.0, le=2.0)
    max_tokens: int = Field(default=1024, ge=1, le=4096)


class SourceResponse(BaseModel):
    """A single cited passage within QuestionResponse.sources."""

    chunk_id: str
    doc_id: str
    text: str
    relevance_score: float = Field(ge=0.0, le=1.0)


class QuestionResponse(BaseModel):
    """Outgoing payload for POST /ask-question."""

    answer: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    is_fallback: bool
    sources: list[SourceResponse]
    response_time_ms: float = Field(ge=0.0)
    conversation_id: str | None = None


# ---------------------------------------------------------------------------
# Health endpoint
# ---------------------------------------------------------------------------


class HealthResponse(BaseModel):
    """Outgoing payload for GET /health."""

    status: str  # "healthy" | "degraded" | "not_ready"
    vector_store: str  # "loaded" | "not_loaded"
    llm_provider: str  # "reachable" | "unreachable"
    database: str  # "connected" | "disconnected"
    uptime_seconds: float = Field(ge=0.0)
    persistence_failure_count: int = Field(ge=0)


# ---------------------------------------------------------------------------
# Evaluate endpoint
# ---------------------------------------------------------------------------


class RegressionFlag(BaseModel):
    """A single metric regression entry."""

    metric: str
    baseline_value: float
    current_value: float
    delta_pct: float


class EvaluateRequest(BaseModel):
    """Incoming payload for POST /evaluate."""

    dataset_path: str | None = None
    k_values: list[int] | None = Field(default=None)
    generate_report: bool = True
    compare_baseline: bool = True


class EvaluateResponse(BaseModel):
    """Outgoing payload for POST /evaluate."""

    retrieval: dict[str, float]
    response_quality: dict[str, float]
    benchmark: dict[str, float]
    regressions: list[RegressionFlag]
    report_path: str | None = None
    total_queries: int


# ---------------------------------------------------------------------------
# Analytics endpoint
# ---------------------------------------------------------------------------


class AnalyticsResponse(BaseModel):
    """Outgoing payload for GET /analytics."""

    total_queries: int = Field(ge=0)
    avg_latency_ms: float = Field(ge=0.0)
    cache_hit_rate: float = Field(ge=0.0, le=1.0)
    top_domains: list[str] = Field(default_factory=list, max_length=10)
    queries_per_day: dict[str, int] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Upload endpoint
# ---------------------------------------------------------------------------


class UploadResponse(BaseModel):
    """Outgoing payload for POST /upload."""

    filename: str
    extension: str
    chunks_added: int = Field(ge=0)
    total_vectors: int = Field(ge=0)
    ingested_at: float = Field(ge=0.0)


class UploadStatusResponse(BaseModel):
    """Outgoing payload for GET /upload/status."""

    total_vectors: int = Field(ge=0)
    allowed_extensions: list[str]
    max_bytes: int = Field(ge=1)
    last_upload: UploadResponse | None = None


# ---------------------------------------------------------------------------
# Error envelope
# ---------------------------------------------------------------------------


class ErrorEnvelope(BaseModel):
    """Consistent error response for all failure modes.

    Constitution Article VII mandates ``{"error", "detail", "status_code"}``.
    """

    error: str
    detail: str
    status_code: int = Field(ge=400, le=599)
