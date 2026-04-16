"""Retrieval request and result Pydantic models for MRAG."""

from __future__ import annotations

from pydantic import BaseModel, Field


class RetrievalRequest(BaseModel):
    """Input to the retrieval pipeline."""

    query: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1)
    score_threshold: float | None = Field(default=None, ge=0.0, le=1.0)
    metadata_filters: dict[str, str] | None = None


class RetrievalResult(BaseModel):
    """Output from the retrieval pipeline for a single matched chunk."""

    chunk_id: str
    doc_id: str
    chunk_text: str
    relevance_score: float = Field(ge=0.0, le=1.0)
    cosine_similarity: float = Field(ge=-1.0, le=1.0)
    question: str
    answer_short: str | None = None
    answer_long: str
    question_type: str
    domain: str
    difficulty: str
    has_short_answer: bool
