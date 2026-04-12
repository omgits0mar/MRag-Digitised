"""SQLAlchemy ORM models for the persistence layer.

Defines QueryRecord, ConversationTurn, and AnalyticsSnapshot.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from mrag.db.base import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class QueryRecord(Base):
    """Persists every question-answer exchange."""

    __tablename__ = "query_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    response_text: Mapped[str] = mapped_column(Text, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    is_fallback: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    embedding_time_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    search_time_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    llm_time_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_time_ms: Mapped[float] = mapped_column(Float, nullable=False)
    cache_hit: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    conversation_id: Mapped[str | None] = mapped_column(
        String(64), nullable=True
    )
    error_indicator: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=_utcnow
    )

    __table_args__ = (
        Index("ix_queryrecord_created_at", "created_at"),
        Index("ix_queryrecord_conversation_id", "conversation_id"),
    )


class ConversationTurn(Base):
    """Tracks individual turns within a multi-turn conversation."""

    __tablename__ = "conversation_turns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    conversation_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    turn_number: Mapped[int] = mapped_column(Integer, nullable=False)
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    response_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=_utcnow
    )

    __table_args__ = (
        Index(
            "ix_convturn_cid_turn",
            "conversation_id",
            "turn_number",
        ),
    )


class AnalyticsSnapshot(Base):
    """Pre-computed or on-demand analytics aggregation over a time period."""

    __tablename__ = "analytics_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    period_start: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    total_queries: Mapped[int] = mapped_column(Integer, nullable=False)
    avg_latency_ms: Mapped[float] = mapped_column(Float, nullable=False)
    cache_hit_rate: Mapped[float] = mapped_column(Float, nullable=False)
    top_domains_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=_utcnow
    )
