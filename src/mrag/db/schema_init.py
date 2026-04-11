"""Idempotent schema creation for the persistence layer."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncEngine

from mrag.db.base import Base


async def create_tables(engine: AsyncEngine) -> None:
    """Idempotent table creation.

    Calls Base.metadata.create_all via run_sync.
    Safe to call multiple times — existing tables are not modified.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
