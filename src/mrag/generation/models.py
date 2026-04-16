"""Pydantic models for the response generation module.

Defines the data structures emitted by the generation pipeline:
SourceCitation, ValidationResult, and GeneratedResponse.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from mrag.cache.models import RequestMetrics


class SourceCitation(BaseModel):
    """A reference to a retrieved passage used in the generated answer.

    Attributes:
        chunk_id: ID of the cited chunk.
        doc_id: Parent document ID.
        chunk_text: Raw text of the passage.
        relevance_score: Retrieval relevance score (0..1).
    """

    chunk_id: str
    doc_id: str
    chunk_text: str
    relevance_score: float = Field(ge=0.0, le=1.0)


class ValidationResult(BaseModel):
    """Output of response-quality validation.

    Attributes:
        confidence_score: Final weighted confidence (0..1).
        retrieval_score_avg: Mean of retrieval scores for the top-K contexts.
        context_overlap: TF-IDF overlap between the answer and the context.
        is_confident: True if confidence_score >= threshold_used.
        threshold_used: Threshold applied at validation time.
    """

    confidence_score: float = Field(ge=0.0, le=1.0)
    retrieval_score_avg: float = Field(ge=0.0, le=1.0)
    context_overlap: float = Field(ge=0.0, le=1.0)
    is_confident: bool
    threshold_used: float = Field(ge=0.0, le=1.0)


class GeneratedResponse(BaseModel):
    """Final output of the generation pipeline.

    Attributes:
        query: Original user query (pre-processing input).
        answer: Generated answer text (or fallback message).
        confidence_score: Confidence in the answer (0..1).
        is_fallback: True if a fallback response was returned.
        sources: Retrieved passages cited in the answer.
        metrics: Per-request timing breakdown.
    """

    query: str
    answer: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    is_fallback: bool = False
    sources: list[SourceCitation] = Field(default_factory=list)
    metrics: RequestMetrics
