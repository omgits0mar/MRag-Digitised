"""Pydantic models for the cache and metrics module.

Defines RequestMetrics — the per-request timing breakdown shared by both
the generation and cache modules.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class RequestMetrics(BaseModel):
    """Per-request timing and cache-attribution data.

    Attributes:
        preprocessing_time_ms: Query normalization + expansion time.
        embedding_time_ms: Query embedding time.
        search_time_ms: FAISS search + re-ranking time.
        llm_time_ms: LLM API call time.
        total_time_ms: End-to-end request time.
        cache_hit: Whether the response or embedding was served from cache.
        cache_type: Which cache layer hit ("embedding", "response", or None).
    """

    preprocessing_time_ms: float = Field(default=0.0, ge=0.0)
    embedding_time_ms: float = Field(default=0.0, ge=0.0)
    search_time_ms: float = Field(default=0.0, ge=0.0)
    llm_time_ms: float = Field(default=0.0, ge=0.0)
    total_time_ms: float = Field(default=0.0, ge=0.0)
    cache_hit: bool = False
    cache_type: str | None = None
