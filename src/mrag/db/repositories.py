"""Repository classes for the persistence layer.

Provides thin data-access objects per entity, each accepting an
``AsyncSession``. Keeps SQLAlchemy out of routes.
"""

from __future__ import annotations

import json
from datetime import datetime

import structlog
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from mrag.db.models import AnalyticsSnapshot, ConversationTurn, QueryRecord

logger = structlog.get_logger(__name__)


class QueryRepository:
    """Data access for QueryRecord."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        query_text: str,
        response_text: str,
        confidence_score: float,
        is_fallback: bool,
        total_time_ms: float,
        cache_hit: bool,
        embedding_time_ms: float | None = None,
        search_time_ms: float | None = None,
        llm_time_ms: float | None = None,
        conversation_id: str | None = None,
        error_indicator: str | None = None,
    ) -> QueryRecord:
        """Insert a new query record."""
        record = QueryRecord(
            query_text=query_text,
            response_text=response_text,
            confidence_score=confidence_score,
            is_fallback=is_fallback,
            total_time_ms=total_time_ms,
            cache_hit=cache_hit,
            embedding_time_ms=embedding_time_ms,
            search_time_ms=search_time_ms,
            llm_time_ms=llm_time_ms,
            conversation_id=conversation_id,
            error_indicator=error_indicator,
        )
        self._session.add(record)
        await self._session.flush()
        return record

    async def get_by_id(self, record_id: int) -> QueryRecord | None:
        """Retrieve a single record by primary key."""
        result = await self._session.execute(
            select(QueryRecord).where(QueryRecord.id == record_id)
        )
        return result.scalar_one_or_none()

    async def list_by_time_range(
        self,
        start: datetime,
        end: datetime,
        limit: int = 1000,
        offset: int = 0,
    ) -> list[QueryRecord]:
        """List records within a time window, ordered by created_at ASC."""
        result = await self._session.execute(
            select(QueryRecord)
            .where(
                QueryRecord.created_at >= start,
                QueryRecord.created_at < end,
            )
            .order_by(QueryRecord.created_at.asc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def count_in_range(self, start: datetime, end: datetime) -> int:
        """Count records in a time window."""
        result = await self._session.execute(
            select(func.count(QueryRecord.id)).where(
                QueryRecord.created_at >= start,
                QueryRecord.created_at < end,
            )
        )
        return result.scalar_one()

    async def avg_latency_in_range(self, start: datetime, end: datetime) -> float:
        """Average total_time_ms in a time window."""
        result = await self._session.execute(
            select(func.avg(QueryRecord.total_time_ms)).where(
                QueryRecord.created_at >= start,
                QueryRecord.created_at < end,
            )
        )
        val = result.scalar_one()
        return float(val) if val is not None else 0.0

    async def cache_hit_rate_in_range(self, start: datetime, end: datetime) -> float:
        """Proportion of cache_hit=True in a time window."""
        total = await self.count_in_range(start, end)
        if total == 0:
            return 0.0
        result = await self._session.execute(
            select(func.count(QueryRecord.id)).where(
                QueryRecord.created_at >= start,
                QueryRecord.created_at < end,
                QueryRecord.cache_hit.is_(True),
            )
        )
        hits = result.scalar_one()
        return hits / total


class ConversationRepository:
    """Data access for ConversationTurn."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_turn(
        self,
        conversation_id: str,
        query_text: str,
        response_text: str,
    ) -> ConversationTurn:
        """Append a new turn to a conversation.

        Automatically determines the next turn_number.
        """
        # Get current max turn_number for this conversation
        result = await self._session.execute(
            select(func.max(ConversationTurn.turn_number)).where(
                ConversationTurn.conversation_id == conversation_id
            )
        )
        max_turn = result.scalar_one_or_none()
        next_turn = (max_turn or 0) + 1

        turn = ConversationTurn(
            conversation_id=conversation_id,
            turn_number=next_turn,
            query_text=query_text,
            response_text=response_text,
        )
        self._session.add(turn)
        await self._session.flush()
        return turn

    async def get_recent_turns(
        self,
        conversation_id: str,
        limit: int = 100,
    ) -> list[ConversationTurn]:
        """Retrieve the most recent turns in chronological order.

        Issues DESC query + Python reverse for O(log n + k) performance.
        """
        result = await self._session.execute(
            select(ConversationTurn)
            .where(ConversationTurn.conversation_id == conversation_id)
            .order_by(desc(ConversationTurn.turn_number))
            .limit(limit)
        )
        turns = list(result.scalars().all())
        turns.reverse()
        return turns

    async def get_turn_count(self, conversation_id: str) -> int:
        """Count total turns for a conversation."""
        result = await self._session.execute(
            select(func.count(ConversationTurn.id)).where(
                ConversationTurn.conversation_id == conversation_id
            )
        )
        return result.scalar_one()


class AnalyticsRepository:
    """Data access for analytics aggregation."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def compute_analytics(
        self,
        start: datetime,
        end: datetime,
    ) -> dict:
        """Compute real-time analytics from QueryRecord table.

        Performance: Must complete in < 1 second for up to 100K records (SC-005).
        """
        total = await self._session.execute(
            select(func.count(QueryRecord.id)).where(
                QueryRecord.created_at >= start,
                QueryRecord.created_at < end,
            )
        )
        total_queries = total.scalar_one()

        if total_queries == 0:
            return {
                "total_queries": 0,
                "avg_latency_ms": 0.0,
                "cache_hit_rate": 0.0,
                "top_domains": [],
                "queries_per_day": {},
            }

        avg_result = await self._session.execute(
            select(func.avg(QueryRecord.total_time_ms)).where(
                QueryRecord.created_at >= start,
                QueryRecord.created_at < end,
            )
        )
        avg_latency = float(avg_result.scalar_one())

        hits_result = await self._session.execute(
            select(func.count(QueryRecord.id)).where(
                QueryRecord.created_at >= start,
                QueryRecord.created_at < end,
                QueryRecord.cache_hit.is_(True),
            )
        )
        hits = hits_result.scalar_one()
        cache_hit_rate = hits / total_queries

        # Queries per day using SQLite/MySQL compatible date function
        day_result = await self._session.execute(
            select(
                func.strftime("%Y-%m-%d", QueryRecord.created_at).label("day"),
                func.count(QueryRecord.id).label("cnt"),
            )
            .where(
                QueryRecord.created_at >= start,
                QueryRecord.created_at < end,
            )
            .group_by("day")
            .order_by("day")
        )
        queries_per_day = {row.day: row.cnt for row in day_result.all()}

        return {
            "total_queries": total_queries,
            "avg_latency_ms": avg_latency,
            "cache_hit_rate": cache_hit_rate,
            "top_domains": [],  # placeholder — future domain tagging
            "queries_per_day": queries_per_day,
        }

    async def save_snapshot(
        self,
        analytics: dict,
        period_start: datetime,
        period_end: datetime,
    ) -> AnalyticsSnapshot:
        """Persist an analytics snapshot for historical tracking."""
        snapshot = AnalyticsSnapshot(
            period_start=period_start,
            period_end=period_end,
            total_queries=analytics.get("total_queries", 0),
            avg_latency_ms=analytics.get("avg_latency_ms", 0.0),
            cache_hit_rate=analytics.get("cache_hit_rate", 0.0),
            top_domains_json=json.dumps(analytics.get("top_domains", [])),
        )
        self._session.add(snapshot)
        await self._session.flush()
        return snapshot
