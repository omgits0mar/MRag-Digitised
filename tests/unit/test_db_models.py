"""Unit tests for SQLAlchemy ORM models."""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from mrag.db.base import Base
from mrag.db.models import AnalyticsSnapshot, ConversationTurn, QueryRecord


@pytest.fixture
async def engine():
    eng = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest.fixture
async def session(engine):
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as sess:
        yield sess


class TestQueryRecord:
    async def test_create_and_read(self, session: AsyncSession):
        record = QueryRecord(
            query_text="What is DNA?",
            response_text="DNA is a molecule.",
            confidence_score=0.85,
            is_fallback=False,
            total_time_ms=1500.0,
            cache_hit=False,
        )
        session.add(record)
        await session.flush()

        assert record.id is not None
        assert record.query_text == "What is DNA?"
        assert record.confidence_score == 0.85
        assert record.created_at is not None

    async def test_optional_fields(self, session: AsyncSession):
        record = QueryRecord(
            query_text="test",
            response_text="answer",
            confidence_score=0.5,
            is_fallback=True,
            total_time_ms=200.0,
            cache_hit=True,
            conversation_id="conv-001",
            embedding_time_ms=100.0,
            search_time_ms=50.0,
            llm_time_ms=300.0,
        )
        session.add(record)
        await session.flush()

        assert record.conversation_id == "conv-001"
        assert record.embedding_time_ms == 100.0

    async def test_indexes_exist(self):
        index_names = {idx.name for idx in QueryRecord.__table__.indexes}
        assert "ix_queryrecord_created_at" in index_names
        assert "ix_queryrecord_conversation_id" in index_names


class TestConversationTurn:
    async def test_create_turn(self, session: AsyncSession):
        turn = ConversationTurn(
            conversation_id="conv-001",
            turn_number=1,
            query_text="What is DNA?",
            response_text="DNA is a molecule.",
        )
        session.add(turn)
        await session.flush()

        assert turn.id is not None
        assert turn.turn_number == 1

    async def test_compound_index(self):
        index_names = {idx.name for idx in ConversationTurn.__table__.indexes}
        assert "ix_convturn_cid_turn" in index_names


class TestAnalyticsSnapshot:
    async def test_create_snapshot(self, session: AsyncSession):
        from datetime import datetime, timezone

        snapshot = AnalyticsSnapshot(
            period_start=datetime(2026, 1, 1, tzinfo=timezone.utc),
            period_end=datetime(2026, 2, 1, tzinfo=timezone.utc),
            total_queries=100,
            avg_latency_ms=1500.0,
            cache_hit_rate=0.35,
        )
        session.add(snapshot)
        await session.flush()

        assert snapshot.id is not None
        assert snapshot.total_queries == 100
