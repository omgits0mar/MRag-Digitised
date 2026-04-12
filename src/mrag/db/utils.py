"""Persistence utilities — safe_persist and failure tracking.

The ``safe_persist`` wrapper is the single enforcement point for FR-012 /
SC-011: persistence failures MUST NOT block the API caller.
"""

from __future__ import annotations

import asyncio

import structlog
from sqlalchemy.exc import SQLAlchemyError

logger = structlog.get_logger(__name__)

_failure_lock = asyncio.Lock()
persistence_failure_count: int = 0


async def _increment_failure_count() -> None:
    """Atomically increment the persistence failure counter."""
    global persistence_failure_count
    async with _failure_lock:
        persistence_failure_count += 1


async def safe_persist(coro, *, operation: str) -> None:
    """Await a persistence coroutine, swallowing and logging any failure.

    Args:
        coro: An awaitable that performs a database write.
        operation: Label for structured logging (e.g., "persist_query").

    Side effects:
        - On success: no-op.
        - On failure: logs error with operation, error_type, error_detail;
          increments persistence_failure_count; does NOT re-raise.
    """
    try:
        await coro
    except SQLAlchemyError as exc:
        await _increment_failure_count()
        logger.error(
            "persistence_failure",
            operation=operation,
            error_type=type(exc).__name__,
            error_detail=str(exc),
            persistence_degraded=True,
        )
    except Exception as exc:
        await _increment_failure_count()
        logger.error(
            "persistence_failure",
            operation=operation,
            error_type=type(exc).__name__,
            error_detail=str(exc),
            persistence_degraded=True,
        )
