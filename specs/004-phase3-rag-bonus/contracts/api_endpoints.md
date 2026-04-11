# Contract: API Endpoints

**Module**: `src/mrag/api/`

## App Factory

```python
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Load heavy resources at startup; dispose at shutdown.

    Populates:
        app.state.pipeline      — MRAGPipeline (Phase 2)
        app.state.db_engine     — AsyncEngine (SQLAlchemy)
        app.state.db_session_factory — async_sessionmaker
        app.state.evaluator     — EvaluationRunner
        app.state.startup_ts    — float (time.time())
    """

def create_app() -> FastAPI:
    """Build and return the FastAPI application.

    Registers lifespan, middleware, CORS, and all route modules.
    OpenAPI docs available at /docs.
    """
```

## Dependency Injection (`dependencies.py`)

```python
from fastapi import Request
from mrag.pipeline import MRAGPipeline
from mrag.db.repositories import QueryRepository, ConversationRepository, AnalyticsRepository
from mrag.evaluation.runner import EvaluationRunner

async def get_pipeline(request: Request) -> MRAGPipeline:
    """Return the pipeline loaded at startup."""

async def get_db_session(request: Request) -> AsyncIterator[AsyncSession]:
    """Yield an async session; commit on success, rollback on error."""

async def get_query_repo(session: AsyncSession = Depends(get_db_session)) -> QueryRepository:
    """Return a QueryRepository bound to the current session."""

async def get_conversation_repo(session: AsyncSession = Depends(get_db_session)) -> ConversationRepository:
    """Return a ConversationRepository bound to the current session."""

async def get_analytics_repo(session: AsyncSession = Depends(get_db_session)) -> AnalyticsRepository:
    """Return an AnalyticsRepository bound to the current session."""

async def get_evaluator(request: Request) -> EvaluationRunner:
    """Return the EvaluationRunner loaded at startup."""
```

## Routes

### POST /ask-question (`routes/ask.py`)

```python
from mrag.api.schemas import QuestionRequest, QuestionResponse, ErrorEnvelope

@router.post(
    "/ask-question",
    response_model=QuestionResponse,
    responses={422: {"model": ErrorEnvelope}, 500: {"model": ErrorEnvelope}},
    summary="Submit a question and receive an AI-generated answer",
)
async def ask_question(
    body: QuestionRequest,
    pipeline: MRAGPipeline = Depends(get_pipeline),
    query_repo: QueryRepository = Depends(get_query_repo),
    conv_repo: ConversationRepository = Depends(get_conversation_repo),
) -> QuestionResponse:
    """Process a question through the full RAG pipeline.

    Flow:
        1. Load conversation history if conversation_id present.
        2. Run MRAGPipeline.ask() with the question.
        3. Persist QueryRecord + ConversationTurn via safe_persist.
        4. Return QuestionResponse.

    Raises:
        422: Malformed request body.
        500: Pipeline failure (after fallback exhausted).
    """
```

**Example request**:
```json
{
  "question": "What is photosynthesis?",
  "conversation_id": null,
  "expand": true,
  "temperature": 0.1,
  "max_tokens": 1024
}
```

**Example response** (200):
```json
{
  "answer": "Photosynthesis is the process by which green plants...",
  "confidence_score": 0.72,
  "is_fallback": false,
  "sources": [
    {
      "chunk_id": "c_00a1b2",
      "doc_id": "d_5f3e1a",
      "text": "Photosynthesis is a process used by plants...",
      "relevance_score": 0.85
    }
  ],
  "response_time_ms": 1842.5,
  "conversation_id": null
}
```

**Example error** (422):
```json
{
  "error": "validation_error",
  "detail": "question: field required",
  "status_code": 422
}
```

---

### GET /health (`routes/health.py`)

```python
from mrag.api.schemas import HealthResponse

@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Check service health and dependency status",
)
async def health_check(
    request: Request,
) -> HealthResponse:
    """Report readiness of all critical dependencies.

    Checks:
        - vector_store: RetrieverService.is_loaded flag
        - llm_provider: cached last_successful_generation_ts within window
        - database: SELECT 1 through async engine
        - uptime: time.time() - app.state.startup_ts
        - persistence_failure_count: module-level counter

    Always returns 200 with status body — never raises HTTP errors.
    Returns within < 1 second.
    """
```

**Example response** (200 — healthy):
```json
{
  "status": "healthy",
  "vector_store": "loaded",
  "llm_provider": "reachable",
  "database": "connected",
  "uptime_seconds": 3642.7,
  "persistence_failure_count": 0
}
```

**Example response** (200 — degraded):
```json
{
  "status": "degraded",
  "vector_store": "loaded",
  "llm_provider": "unreachable",
  "database": "connected",
  "uptime_seconds": 7201.3,
  "persistence_failure_count": 12
}
```

---

### POST /evaluate (`routes/evaluate.py`)

```python
from mrag.api.schemas import EvaluateRequest, EvaluateResponse

@router.post(
    "/evaluate",
    response_model=EvaluateResponse,
    summary="Run the evaluation suite and return metrics",
)
async def run_evaluation(
    body: EvaluateRequest,
    evaluator: EvaluationRunner = Depends(get_evaluator),
) -> EvaluateResponse:
    """Trigger a full evaluation run.

    Flow:
        1. Load dataset from body.dataset_path or default.
        2. Run EvaluationRunner.run_full_evaluation().
        3. Optionally compare against baseline.
        4. Optionally generate HTML report.
        5. Return EvaluateResponse with all metrics.

    Raises:
        422: Malformed request.
        500: Evaluation failure.
    """
```

**Example response** (200):
```json
{
  "retrieval": {
    "precision_at_1": 0.62,
    "precision_at_5": 0.41,
    "recall_at_5": 0.73,
    "recall_at_10": 0.78,
    "mrr": 0.55,
    "map": 0.48
  },
  "response_quality": {
    "bleu": 0.32,
    "rouge_1": 0.51,
    "rouge_2": 0.28,
    "rouge_l": 0.47
  },
  "benchmark": {
    "p50_ms": 1200.0,
    "p95_ms": 2800.0,
    "p99_ms": 3400.0,
    "qps": 0.83
  },
  "regressions": [],
  "report_path": "data/reports/eval_20260409_120000.html",
  "total_queries": 200
}
```

---

### GET /analytics (`routes/analytics.py`)

```python
from mrag.api.schemas import AnalyticsResponse

@router.get(
    "/analytics",
    response_model=AnalyticsResponse,
    summary="Get aggregated query analytics",
)
async def get_analytics(
    start_date: str | None = None,
    end_date: str | None = None,
    analytics_repo: AnalyticsRepository = Depends(get_analytics_repo),
) -> AnalyticsResponse:
    """Aggregate query analytics over a time window.

    Args:
        start_date: ISO 8601 date string (inclusive). Defaults to 30 days ago.
        end_date: ISO 8601 date string (exclusive). Defaults to now.

    Returns:
        AnalyticsResponse with totals, averages, rates, and daily counts.
    """
```

---

## Middleware (`middleware.py`)

```python
async def global_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch all unhandled exceptions and return ErrorEnvelope.

    Maps:
        RequestValidationError → 422
        DatabaseError          → 500 (logged, detail="persistence error")
        EvaluationError        → 500 (logged, detail="evaluation error")
        Exception              → 500 (logged, detail="internal error")
    """
```

## Schemas (`schemas.py`)

All models listed in data-model.md API Entities section. Pydantic v2 `BaseModel` subclasses with `model_config = ConfigDict(from_attributes=True)` where needed for ORM conversion.
