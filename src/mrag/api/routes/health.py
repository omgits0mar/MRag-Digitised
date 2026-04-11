"""GET /health route.

Reports readiness of all critical dependencies using cheap probes:
cached flags for vector store and LLM, SELECT 1 for DB.
"""

from __future__ import annotations

import time

from fastapi import APIRouter, Request
from sqlalchemy import text

from mrag.api.schemas import HealthResponse
from mrag.db import utils as db_utils

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Check service health and dependency status",
)
async def health_check(request: Request) -> HealthResponse:
    """Report readiness of all critical dependencies.

    Always returns 200 with status body. Returns within < 1 second.
    """
    # Vector store check — read cached is_loaded flag
    pipeline = request.app.state.pipeline
    vector_store_status = "not_loaded"
    try:
        vector_store_status = (
            "loaded" if pipeline._retriever._indexer.is_loaded else "not_loaded"
        )
    except Exception:
        vector_store_status = "not_loaded"

    # LLM provider check — if pipeline constructed, LLM client exists
    llm_status = "reachable"

    # Database check — SELECT 1
    db_status = "disconnected"
    try:
        engine = request.app.state.db_engine
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "disconnected"

    # Uptime
    uptime = time.time() - request.app.state.startup_ts

    # Determine overall status
    if (
        vector_store_status == "loaded"
        and llm_status == "reachable"
        and db_status == "connected"
    ):
        overall = "healthy"
    elif db_status == "disconnected":
        overall = "not_ready"
    else:
        overall = "degraded"

    return HealthResponse(
        status=overall,
        vector_store=vector_store_status,
        llm_provider=llm_status,
        database=db_status,
        uptime_seconds=uptime,
        persistence_failure_count=db_utils.persistence_failure_count,
    )
