# Quickstart: Phase 3 RAG Bonus

## Prerequisites

- Phase 1 complete: FAISS index built, metadata store populated
- Phase 2 complete: Query processing, response generation, caching modules functional
- conda environment `mrag` activated
- `.env` file with `LLM_API_KEY` set (Groq API key)

## Setup

```bash
# Activate environment
conda activate mrag

# Install updated dependencies (adds aiosqlite, sacrebleu, rouge-score, matplotlib)
pip install -e ".[dev]"

# Verify Phase 1/2 artifacts exist
ls data/processed/*.faiss data/processed/*_metadata.json
```

## Configuration

Key `.env` settings for Phase 3 (add to existing `.env`):

```bash
# === Already present from Phase 2 ===
LLM_API_KEY=gsk_your_groq_api_key_here

# === API (Feature 007) ===
API_HOST=0.0.0.0
API_PORT=8000
API_CORS_ORIGINS=["http://localhost:3000"]
API_REQUEST_TIMEOUT_SECONDS=30

# === Database (Feature 008) ===
# Default: SQLite for local dev
DATABASE_URL=sqlite+aiosqlite:///mrag.db
# Production: MySQL
# DATABASE_URL=mysql+aiomysql://user:pass@host:3306/mrag?charset=utf8mb4
DB_ECHO=false

# === Evaluation (Feature 009) ===
EVAL_HELDOUT_PATH=data/processed/eval.jsonl
EVAL_BASELINE_PATH=data/evaluation/baseline_metrics.json
EVAL_REPORT_DIR=data/reports
EVAL_K_VALUES=[1,3,5,10]
EVAL_BENCHMARK_WORKLOAD_SIZE=100
EVAL_REGRESSION_THRESHOLD=0.05
```

## Running the API Server

```bash
# Start the API with uvicorn
uvicorn mrag.api.app:create_app --factory --host 0.0.0.0 --port 8000 --reload

# Or via module
python -m uvicorn mrag.api.app:create_app --factory --port 8000
```

## Quick Verification

### 1. Health Check

```bash
curl http://localhost:8000/health | python -m json.tool
```

Expected:
```json
{
  "status": "healthy",
  "vector_store": "loaded",
  "llm_provider": "reachable",
  "database": "connected",
  "uptime_seconds": 5.2,
  "persistence_failure_count": 0
}
```

### 2. Ask a Question

```bash
curl -X POST http://localhost:8000/ask-question \
  -H "Content-Type: application/json" \
  -d '{"question": "What is photosynthesis?"}' | python -m json.tool
```

Expected: JSON response with `answer`, `confidence_score`, `sources`, `response_time_ms`.

### 3. Multi-Turn Conversation

```bash
# First turn
curl -X POST http://localhost:8000/ask-question \
  -H "Content-Type: application/json" \
  -d '{"question": "What is DNA?", "conversation_id": "conv-001"}'

# Follow-up turn (should resolve "it" to "DNA")
curl -X POST http://localhost:8000/ask-question \
  -H "Content-Type: application/json" \
  -d '{"question": "How is it structured?", "conversation_id": "conv-001"}'
```

### 4. Interactive Docs

Open `http://localhost:8000/docs` in a browser to see the Swagger UI with all endpoints and schemas.

### 5. Database Verification

```python
import asyncio
from mrag.db.engine import create_db_engine, create_session_factory
from mrag.db.repositories import QueryRepository
from mrag.config import get_settings

async def check_db():
    settings = get_settings()
    engine = create_db_engine(settings.database_url.get_secret_value())
    session_factory = create_session_factory(engine)
    async with session_factory() as session:
        repo = QueryRepository(session)
        records = await repo.list_by_time_range(
            start=datetime.min, end=datetime.utcnow(), limit=5
        )
        print(f"Found {len(records)} records")
    await engine.dispose()

asyncio.run(check_db())
```

### 6. Run Evaluation (Standalone)

```python
import asyncio
from mrag.evaluation.runner import EvaluationRunner
# Assumes pipeline is built (see Phase 2 quickstart for pipeline construction)

async def run_eval():
    runner = EvaluationRunner(pipeline=pipeline)
    report = await runner.run_full_evaluation()
    print(f"Precision@5: {report.retrieval.precision_at_k[5]:.3f}")
    print(f"BLEU: {report.response_quality.bleu:.3f}")
    print(f"p95 latency: {report.benchmark.p95_ms:.0f}ms")
    if report.baseline_comparison:
        print(f"Regressions: {report.baseline_comparison.has_regressions}")
    if report.report_path:
        print(f"Report: {report.report_path}")

asyncio.run(run_eval())
```

### 7. Analytics

```bash
# After processing some queries through the API
curl "http://localhost:8000/analytics?start_date=2026-04-01&end_date=2026-04-10" \
  | python -m json.tool
```

## Running Tests

```bash
# Unit tests only (no API server or LLM key needed)
pytest tests/unit/test_api_schemas.py tests/unit/test_db_models.py tests/unit/test_retrieval_metrics.py tests/unit/test_response_metrics.py -v

# DB integration tests (uses in-memory SQLite)
pytest tests/integration/test_db_integration.py tests/integration/test_conversation_flow.py -v

# API integration tests (requires LLM_API_KEY and Phase 1 index)
pytest tests/integration/test_api_ask.py tests/integration/test_api_health.py -v

# Evaluation integration test (requires LLM_API_KEY, Phase 1 index, eval dataset)
pytest tests/integration/test_evaluation_runner.py -v

# All tests
make test
```
