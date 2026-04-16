"""Unit tests for database repositories against in-memory SQLite."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from mrag.db.base import Base
from mrag.db.repositories import (
    AnalyticsRepository,
    ConversationRepository,
    QueryRepository,
)


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


class TestQueryRepository:
    async def test_create_and_get(self, session: AsyncSession):
        repo = QueryRepository(session)
        record = await repo.create(
            query_text="What is DNA?",
            response_text="DNA is a molecule.",
            confidence_score=0.85,
            is_fallback=False,
            total_time_ms=1500.0,
            cache_hit=False,
        )
        assert record.id is not None

        fetched = await repo.get_by_id(record.id)
        assert fetched is not None
        assert fetched.query_text == "What is DNA?"

    async def test_list_by_time_range(self, session: AsyncSession):
        repo = QueryRepository(session)
        await repo.create(
            query_text="q1",
            response_text="a1",
            confidence_score=0.8,
            is_fallback=False,
            total_time_ms=100.0,
            cache_hit=False,
        )
        await repo.create(
            query_text="q2",
            response_text="a2",
            confidence_score=0.9,
            is_fallback=False,
            total_time_ms=200.0,
            cache_hit=False,
        )

        start = datetime.now(timezone.utc) - timedelta(hours=1)
        end = datetime.now(timezone.utc) + timedelta(hours=1)
        records = await repo.list_by_time_range(start, end)
        assert len(records) == 2

    async def test_count_in_range(self, session: AsyncSession):
        repo = QueryRepository(session)
        await repo.create(
            query_text="q",
            response_text="a",
            confidence_score=0.5,
            is_fallback=False,
            total_time_ms=100.0,
            cache_hit=False,
        )
        start = datetime.now(timezone.utc) - timedelta(hours=1)
        end = datetime.now(timezone.utc) + timedelta(hours=1)
        count = await repo.count_in_range(start, end)
        assert count == 1

    async def test_avg_latency(self, session: AsyncSession):
        repo = QueryRepository(session)
        await repo.create("q1", "a1", 0.5, False, 100.0, False)
        await repo.create("q2", "a2", 0.5, False, 300.0, False)

        start = datetime.now(timezone.utc) - timedelta(hours=1)
        end = datetime.now(timezone.utc) + timedelta(hours=1)
        avg = await repo.avg_latency_in_range(start, end)
        assert avg == 200.0

    async def test_cache_hit_rate(self, session: AsyncSession):
        repo = QueryRepository(session)
        await repo.create("q1", "a1", 0.5, False, 100.0, True)
        await repo.create("q2", "a2", 0.5, False, 100.0, False)

        start = datetime.now(timezone.utc) - timedelta(hours=1)
        end = datetime.now(timezone.utc) + timedelta(hours=1)
        rate = await repo.cache_hit_rate_in_range(start, end)
        assert rate == 0.5


class TestConversationRepository:
    async def test_create_turn(self, session: AsyncSession):
        repo = ConversationRepository(session)
        turn = await repo.create_turn("conv-001", "Hello", "Hi there")
        assert turn.turn_number == 1

    async def test_sequential_turns(self, session: AsyncSession):
        repo = ConversationRepository(session)
        t1 = await repo.create_turn("conv-001", "Hello", "Hi")
        t2 = await repo.create_turn("conv-001", "How are you?", "Fine")
        assert t1.turn_number == 1
        assert t2.turn_number == 2

    async def test_get_recent_turns(self, session: AsyncSession):
        repo = ConversationRepository(session)
        await repo.create_turn("conv-001", "Q1", "A1")
        await repo.create_turn("conv-001", "Q2", "A2")
        await repo.create_turn("conv-001", "Q3", "A3")

        turns = await repo.get_recent_turns("conv-001", limit=2)
        assert len(turns) == 2
        # Should be in chronological order (oldest first)
        assert turns[0].query_text == "Q2"
        assert turns[1].query_text == "Q3"

    async def test_get_turn_count(self, session: AsyncSession):
        repo = ConversationRepository(session)
        await repo.create_turn("conv-001", "Q1", "A1")
        await repo.create_turn("conv-001", "Q2", "A2")
        count = await repo.get_turn_count("conv-001")
        assert count == 2


class TestAnalyticsRepository:
    async def test_empty_analytics(self, session: AsyncSession):
        repo = AnalyticsRepository(session)
        start = datetime.now(timezone.utc) - timedelta(days=1)
        end = datetime.now(timezone.utc)
        analytics = await repo.compute_analytics(start, end)
        assert analytics["total_queries"] == 0

    async def test_populated_analytics(self, session: AsyncSession):
        query_repo = QueryRepository(session)
        await query_repo.create("q1", "a1", 0.5, False, 100.0, True)
        await query_repo.create("q2", "a2", 0.5, False, 200.0, False)

        analytics_repo = AnalyticsRepository(session)
        start = datetime.now(timezone.utc) - timedelta(hours=1)
        end = datetime.now(timezone.utc) + timedelta(hours=1)
        analytics = await analytics_repo.compute_analytics(start, end)

        assert analytics["total_queries"] == 2
        assert analytics["avg_latency_ms"] == 150.0
        assert analytics["cache_hit_rate"] == 0.5
