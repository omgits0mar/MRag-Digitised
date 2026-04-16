"""FastAPI dependency injection providers.

Routes access heavy resources (pipeline, DB sessions, repos, evaluator)
through these providers, all of which read from ``app.state`` populated
by the lifespan handler.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from mrag.db.repositories import (
    AnalyticsRepository,
    ConversationRepository,
    QueryRepository,
)
from mrag.evaluation.runner import EvaluationRunner
from mrag.pipeline import MRAGPipeline


async def get_pipeline(request: Request) -> MRAGPipeline:
    """Return the pipeline loaded at startup."""
    return request.app.state.pipeline


async def get_db_session(request: Request) -> AsyncGenerator[AsyncSession, None]:
    """Yield an async session; commit on success, rollback on error."""
    session_factory: async_sessionmaker[AsyncSession] = (
        request.app.state.db_session_factory
    )
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_query_repo(
    session: AsyncSession = Depends(get_db_session),
) -> QueryRepository:
    """Return a QueryRepository bound to the current session."""
    return QueryRepository(session)


async def get_conversation_repo(
    session: AsyncSession = Depends(get_db_session),
) -> ConversationRepository:
    """Return a ConversationRepository bound to the current session."""
    return ConversationRepository(session)


async def get_analytics_repo(
    session: AsyncSession = Depends(get_db_session),
) -> AnalyticsRepository:
    """Return an AnalyticsRepository bound to the current session."""
    return AnalyticsRepository(session)


async def get_evaluator(request: Request) -> EvaluationRunner:
    """Return the EvaluationRunner loaded at startup."""
    return request.app.state.evaluator
