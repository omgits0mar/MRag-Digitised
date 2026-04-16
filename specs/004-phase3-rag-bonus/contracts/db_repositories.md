# Contract: Database Repositories

**Module**: `src/mrag/db/`

## Engine & Session (`engine.py`)

```python
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

def create_db_engine(database_url: str, echo: bool = False) -> AsyncEngine:
    """Create an async SQLAlchemy engine from the given URL.

    Supports:
        - sqlite+aiosqlite:///path   (local dev)
        - mysql+aiomysql://...       (production)

    Args:
        database_url: Full SQLAlchemy async connection URL.
        echo: If True, log all SQL statements.

    Returns:
        Configured AsyncEngine.
    """

def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Create an async session factory bound to the engine.

    Sessions expire on commit and auto-flush.
    """

async def init_db(engine: AsyncEngine) -> None:
    """Create all tables idempotently via Base.metadata.create_all.

    Called once at startup via the lifespan handler.
    """
```

## Base (`base.py`)

```python
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""
```

## ORM Models (`models.py`)

See data-model.md Persistence Entities section for full column definitions.

```python
from mrag.db.base import Base

class QueryRecord(Base):
    __tablename__ = "query_records"
    # columns: id, query_text, response_text, confidence_score, is_fallback,
    #          embedding_time_ms, search_time_ms, llm_time_ms, total_time_ms,
    #          cache_hit, conversation_id, error_indicator, created_at

class ConversationTurn(Base):
    __tablename__ = "conversation_turns"
    # columns: id, conversation_id, turn_number, query_text, response_text, created_at
    # compound index: (conversation_id, turn_number DESC)

class AnalyticsSnapshot(Base):
    __tablename__ = "analytics_snapshots"
    # columns: id, period_start, period_end, total_queries, avg_latency_ms,
    #          cache_hit_rate, top_domains_json, created_at
```

## Repositories (`repositories.py`)

### QueryRepository

```python
class QueryRepository:
    """Data access for QueryRecord."""

    def __init__(self, session: AsyncSession) -> None: ...

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
        """Insert a new query record.

        Returns:
            The persisted QueryRecord with id and created_at populated.
        """

    async def get_by_id(self, record_id: int) -> QueryRecord | None:
        """Retrieve a single record by primary key."""

    async def list_by_time_range(
        self,
        start: datetime,
        end: datetime,
        limit: int = 1000,
        offset: int = 0,
    ) -> list[QueryRecord]:
        """List records within a time window, ordered by created_at ASC.

        Uses the ix_queryrecord_created_at index.
        """

    async def count_in_range(self, start: datetime, end: datetime) -> int:
        """Count records in a time window (for analytics)."""

    async def avg_latency_in_range(self, start: datetime, end: datetime) -> float:
        """Average total_time_ms in a time window."""

    async def cache_hit_rate_in_range(self, start: datetime, end: datetime) -> float:
        """Proportion of cache_hit=True in a time window."""
```

### ConversationRepository

```python
class ConversationRepository:
    """Data access for ConversationTurn."""

    def __init__(self, session: AsyncSession) -> None: ...

    async def create_turn(
        self,
        conversation_id: str,
        query_text: str,
        response_text: str,
    ) -> ConversationTurn:
        """Append a new turn to a conversation.

        Automatically determines the next turn_number by reading the
        current max turn_number for the conversation_id.

        Returns:
            The persisted ConversationTurn.
        """

    async def get_recent_turns(
        self,
        conversation_id: str,
        limit: int = 100,
    ) -> list[ConversationTurn]:
        """Retrieve the most recent turns for a conversation.

        Issues:
            SELECT ... WHERE conversation_id = :cid
            ORDER BY turn_number DESC LIMIT :n

        Returns turns in chronological order (reversed from DESC query).
        Uses compound index ix_convturn_cid_turn.

        Args:
            conversation_id: The conversation identifier.
            limit: Maximum turns to return (default 100, per FR-011).

        Returns:
            List of ConversationTurn in chronological order (oldest first).
        """

    async def get_turn_count(self, conversation_id: str) -> int:
        """Count total turns for a conversation."""
```

### AnalyticsRepository

```python
class AnalyticsRepository:
    """Data access for analytics aggregation."""

    def __init__(self, session: AsyncSession) -> None: ...

    async def compute_analytics(
        self,
        start: datetime,
        end: datetime,
    ) -> dict:
        """Compute real-time analytics from QueryRecord table.

        Returns:
            {
                "total_queries": int,
                "avg_latency_ms": float,
                "cache_hit_rate": float,
                "top_domains": list[str],       # placeholder — future domain tagging
                "queries_per_day": dict[str, int],  # "YYYY-MM-DD" → count
            }

        Performance: Must complete in < 1 second for up to 100K records (SC-005).
        Uses indexed created_at column and aggregate SQL functions.
        """

    async def save_snapshot(
        self,
        analytics: dict,
        period_start: datetime,
        period_end: datetime,
    ) -> AnalyticsSnapshot:
        """Persist an analytics snapshot for historical tracking."""
```

## Utilities (`utils.py`)

```python
import structlog

logger = structlog.get_logger(__name__)

# Module-level counter for degraded persistence (read by /health)
persistence_failure_count: int = 0

async def safe_persist(coro, *, operation: str) -> None:
    """Await a persistence coroutine, swallowing and logging any failure.

    Args:
        coro: An awaitable that performs a database write.
        operation: Label for structured logging (e.g., "persist_query").

    Side effects:
        - On success: no-op.
        - On failure: logs error with operation, error_type, error_detail;
          increments persistence_failure_count; does NOT re-raise.

    This is the single enforcement point for FR-012 / SC-011:
    persistence failures MUST NOT block the API caller.
    """
```

## Schema Init (`schema_init.py`)

```python
async def create_tables(engine: AsyncEngine) -> None:
    """Idempotent table creation.

    Calls Base.metadata.create_all via run_sync.
    Safe to call multiple times — existing tables are not modified.
    """
```
