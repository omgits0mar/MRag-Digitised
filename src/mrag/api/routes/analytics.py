"""GET /analytics route.

Aggregated usage analytics queryable via GET /analytics.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query

from mrag.api.dependencies import get_analytics_repo
from mrag.api.schemas import AnalyticsResponse
from mrag.db.repositories import AnalyticsRepository

router = APIRouter(tags=["analytics"])


@router.get(
    "/analytics",
    response_model=AnalyticsResponse,
    summary="Get aggregated query analytics",
)
async def get_analytics(
    start_date: str | None = Query(
        default=None, description="ISO 8601 date (inclusive)"
    ),
    end_date: str | None = Query(default=None, description="ISO 8601 date (exclusive)"),
    analytics_repo: AnalyticsRepository = Depends(get_analytics_repo),
) -> AnalyticsResponse:
    """Aggregate query analytics over a time window.

    Defaults to last 30 days if no dates provided.
    """
    now = datetime.now(timezone.utc)

    if end_date:
        end = datetime.fromisoformat(end_date).replace(tzinfo=timezone.utc)
    else:
        end = now

    if start_date:
        start = datetime.fromisoformat(start_date).replace(tzinfo=timezone.utc)
    else:
        start = end - timedelta(days=30)

    analytics = await analytics_repo.compute_analytics(start, end)

    return AnalyticsResponse(
        total_queries=analytics["total_queries"],
        avg_latency_ms=analytics["avg_latency_ms"],
        cache_hit_rate=analytics["cache_hit_rate"],
        top_domains=analytics.get("top_domains", []),
        queries_per_day=analytics.get("queries_per_day", {}),
    )
