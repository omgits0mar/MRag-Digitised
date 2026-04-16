"""Async SQLAlchemy engine and session factory.

Supports ``sqlite+aiosqlite:///`` for local dev and
``mysql+aiomysql://`` for production via the same code path.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from mrag.db.base import Base


def create_db_engine(database_url: str, echo: bool = False) -> AsyncEngine:
    """Create an async SQLAlchemy engine from the given URL.

    Args:
        database_url: Full SQLAlchemy async connection URL.
        echo: If True, log all SQL statements.

    Returns:
        Configured AsyncEngine.
    """
    return create_async_engine(database_url, echo=echo)


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Create an async session factory bound to the engine.

    Sessions expire on commit and auto-flush.
    """
    return async_sessionmaker(engine, expire_on_commit=True)


async def init_db(engine: AsyncEngine) -> None:
    """Create all tables idempotently via Base.metadata.create_all.

    Called once at startup via the lifespan handler.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
