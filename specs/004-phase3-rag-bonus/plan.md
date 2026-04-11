# Implementation Plan: Phase 3 RAG Bonus — API Surface, Persistence & Evaluation Framework

**Branch**: `004-phase3-rag-bonus` | **Date**: 2026-04-09 | **Spec**: specs/004-phase3-rag-bonus/spec.md
**Input**: Feature specification from `/specs/004-phase3-rag-bonus/spec.md`
**Constitution Version**: 1.0.0

## Summary

Phase 3 bundles the three remaining "bonus" modules that turn the Phase 1/2 library into a deliverable service: (1) a FastAPI HTTP surface exposing `POST /ask-question`, `GET /health`, and `POST /evaluate`, wired to the existing `MRAGPipeline.ask()` via async dependency injection; (2) an async SQLAlchemy persistence layer storing every query/response exchange, conversation turn, and analytics snapshot, with SQLite for local dev and MySQL-compatible URLs for production via the same code path; (3) a self-contained evaluation framework computing precision@K, recall@K, MRR, MAP, BLEU, ROUGE-1/2/L, and p50/p95/p99 latency benchmarks, rendered to a self-contained HTML report with matplotlib charts. The evaluation dataset is derived from the Phase 1 eval split (`data/processed/eval.jsonl`), itself produced by the deterministic 90/10 train/eval split of `Natural-Questions-Filtered.csv` (~86,212 rows). Each `ProcessedDocument` in the eval split already carries its chunk IDs (used as the ground-truth relevant set for precision@K/recall@K) and its `answer_short` field (used as the reference answer for BLEU/ROUGE). All modules run on Apple Silicon CPU with no new GPU dependencies. Persistence failures never block the API caller — the service returns the in-memory response and logs the persistence error.

## Technical Context

**Language/Version**: Python 3.10+ (conda environment `mrag`)
**Primary Dependencies**: fastapi 0.115.12, uvicorn 0.34.2, sqlalchemy 2.0.41, aiosqlite (new), scikit-learn 1.6.1, sacrebleu (new), rouge-score (new), matplotlib (new), pydantic 2.11.3, httpx 0.28.1, structlog 25.2.0 — plus existing Phase 1/2 stack (sentence-transformers 4.1.0, faiss-cpu 1.11.0, Jinja2 3.1.6)
**Storage**: SQLite via `aiosqlite` driver for local dev; MySQL-compatible URL via `aiomysql` (optional, not installed by default) for production — same async SQLAlchemy code path; Phase 1 FAISS index (`.faiss`) + JSON metadata files remain the retrieval store
**Testing**: pytest 8.3.5, pytest-asyncio 0.26.0 (existing), `httpx.AsyncClient` + FastAPI `TestClient` for API tests, in-memory SQLite for DB tests
**Target Platform**: macOS Apple Silicon (M-series), CPU-only; service deployable as a single uvicorn process
**Project Type**: Web service (library + HTTP API) — extends the existing `src/mrag/` library with an `api/` entrypoint plus `db/` and `evaluation/` support modules
**Performance Goals**: p95 end-to-end < 3s (SC-001), persistence overhead < 50ms (SC-004), health endpoint < 1s (SC-003), analytics query < 1s over 100K records (SC-005), evaluation benchmark variance < 10% (SC-008)
**Constraints**: No CUDA/NVIDIA GPU, persistence outages MUST NOT block API responses (FR-012), credentials via env vars only (FR-014), evaluation runnable standalone without the API process (FR-022)
**Scale/Scope**: ~86K Q&A pairs indexed in Phase 1; 100K persisted query records per analytics window; 100 turns per conversation window; 1K-query benchmark workloads

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Article | Requirement | Status | Notes |
|---------|-------------|--------|-------|
| I — Modular Architecture | Each component is an independent module | PASS | Three new modules (`api/`, `db/`, `evaluation/`) with explicit I/O contracts; each importable standalone, with no circular imports |
| II — Data Integrity | Validated preprocessing pipeline | PASS | API boundary validates via Pydantic; persistence layer validates via SQLAlchemy column constraints; evaluation dataset loader validates held-out records at ingest |
| III — Multilingual-First | Unicode-safe, UTF-8 throughout | PASS | API accepts UTF-8 JSON; database columns declared as TEXT/VARCHAR with utf8mb4 collation for MySQL; evaluation metrics tokenize on whitespace with Unicode-safe comparison |
| IV — Retrieval Quality > Speed | Ranking, expansion, metrics | PASS | Evaluation module provides the regression gate mandated by Article IV; all retrieval changes are measurable via precision@K/recall@K against the held-out set |
| V — LLM as Replaceable Contract | BaseLLMClient, externalized templates | PASS | API layer consumes the existing `MRAGPipeline` (which owns `BaseLLMClient`); no direct LLM calls from API routes or evaluation runner; health endpoint pings the client via the abstraction |
| VI — Testing | Unit + integration + evaluation | PASS | Unit tests per new module; API integration tests via `TestClient`; DB integration tests via in-memory SQLite; evaluation framework itself is the Article VI deliverable |
| VII — API Standards | FastAPI, Pydantic, consistent errors, OpenAPI, health | PASS | This feature *is* the Article VII implementation. Error envelope `{"error","detail","status_code"}`, OpenAPI at `/docs`, health endpoint reports vector store / LLM / DB / uptime |
| VIII — Performance & Caching | Metrics on every request, LRU/TTL, batch | PASS | Inherits Phase 2 `MetricsCollector`; every API request persists per-stage timing via `QueryRecord`; analytics repository uses indexed columns for fast aggregation |
| IX — Code Quality | Type hints, black, ruff, structured logging, secrets via env | PASS | All new modules follow existing standards; database credentials via `DATABASE_URL` env var (already in `Settings`); no print statements |
| X — Documentation Separation | Spec = WHAT, Plan = HOW | PASS | Spec is technology-agnostic; this plan holds all framework and library decisions |

**No violations.** Every Phase 3 module maps 1:1 to a constitution article and closes an explicit gate (Article VI evaluation, Article VII API standards, Article I modularity of the DB layer). The plan intentionally reuses — rather than duplicates — Phase 2 services via dependency injection.

## Project Structure

### Documentation (this feature)

```text
specs/004-phase3-rag-bonus/
├── plan.md              # This file (/speckit.plan output)
├── research.md          # Phase 0 output (/speckit.plan)
├── data-model.md        # Phase 1 output (/speckit.plan)
├── quickstart.md        # Phase 1 output (/speckit.plan)
├── contracts/           # Phase 1 output (/speckit.plan)
│   ├── api_endpoints.md
│   ├── db_repositories.md
│   └── evaluation_runner.md
├── checklists/
│   └── requirements.md  # Spec quality checklist (already passing)
└── tasks.md             # Phase 2 output (/speckit.tasks — NOT created here)
```

### Source Code (repository root)

```text
src/mrag/
├── api/                        # Feature 007 — FastAPI Integration
│   ├── __init__.py
│   ├── app.py                  # FastAPI app factory + lifespan (loads index, LLM, DB at startup)
│   ├── dependencies.py         # DI providers: get_pipeline, get_query_repo, get_evaluator
│   ├── schemas.py              # Pydantic request/response models (QuestionRequest, QuestionResponse, HealthResponse, EvaluateRequest, EvaluateResponse, ErrorEnvelope, AnalyticsResponse)
│   ├── middleware.py           # Global error handler → ErrorEnvelope, CORS, structured access logging
│   └── routes/
│       ├── __init__.py
│       ├── ask.py              # POST /ask-question (wired to MRAGPipeline + QueryRepository)
│       ├── health.py           # GET /health (probes vector store, LLM, DB)
│       ├── evaluate.py         # POST /evaluate (triggers EvaluationRunner)
│       └── analytics.py        # GET /analytics (AnalyticsRepository aggregation)
│
├── db/                         # Feature 008 — Database Integration
│   ├── __init__.py
│   ├── engine.py               # create_async_engine + async_sessionmaker; session context manager
│   ├── base.py                 # DeclarativeBase + shared metadata
│   ├── models.py               # QueryRecord, ConversationTurn, AnalyticsSnapshot ORM models
│   ├── repositories.py         # QueryRepository, ConversationRepository, AnalyticsRepository
│   ├── schema_init.py          # Idempotent schema creation (metadata.create_all) — no Alembic needed in Phase 3
│   └── utils.py                # Async retry wrapper, safe_persist decorator (never raises to API)
│
├── evaluation/                 # Feature 009 — Evaluation Framework
│   ├── __init__.py
│   ├── models.py               # EvaluationDataset, EvaluationQuery, RetrievalMetrics, ResponseQualityMetrics, BenchmarkResult, EvaluationReport
│   ├── dataset_loader.py       # Load Phase 1 eval split (data/processed/eval.jsonl) and convert ProcessedDocument → EvaluationQuery
│   ├── retrieval_metrics.py    # precision@K, recall@K, MRR, MAP — validated against sklearn where applicable
│   ├── response_metrics.py     # BLEU (sacrebleu), ROUGE-1/2/L (rouge-score)
│   ├── benchmarks.py           # run_benchmark(pipeline, queries) → BenchmarkResult with p50/p95/p99/qps
│   ├── baseline.py             # Baseline comparison: load prior metrics, flag regressions
│   ├── report_generator.py     # matplotlib chart generation + Jinja2 HTML template → single self-contained report
│   └── runner.py               # EvaluationRunner.run_full_evaluation() orchestrating the suite
│
├── cache/                      # Existing Phase 2 (unchanged)
├── generation/                 # Existing Phase 2 (unchanged)
├── query/                      # Existing Phase 2 (unchanged)
├── retrieval/                  # Existing Phase 1 (unchanged)
├── data/                       # Existing Phase 1 (unchanged)
├── embeddings/                 # Existing Phase 1 (unchanged)
├── pipeline.py                 # Existing Phase 2 MRAGPipeline (unchanged — consumed by API routes)
├── config.py                   # Existing — add Phase 3 fields (see Config Additions)
├── exceptions.py               # Existing — add DatabaseError, EvaluationError
└── logging.py                  # Existing (unchanged)

prompts/templates/              # Existing (unchanged)
├── report.html.j2              # NEW — Jinja2 template for evaluation HTML report
└── ... (existing Phase 2 templates)

tests/
├── unit/
│   ├── test_api_schemas.py
│   ├── test_api_middleware.py
│   ├── test_db_models.py
│   ├── test_db_repositories.py
│   ├── test_retrieval_metrics.py
│   ├── test_response_metrics.py
│   ├── test_benchmarks.py
│   ├── test_baseline.py
│   └── test_report_generator.py
├── integration/
│   ├── test_api_ask.py         # POST /ask-question end-to-end
│   ├── test_api_health.py      # GET /health with simulated degraded deps
│   ├── test_api_evaluate.py    # POST /evaluate end-to-end
│   ├── test_api_analytics.py   # GET /analytics over persisted records
│   ├── test_db_integration.py  # API → DB persistence flow
│   ├── test_conversation_flow.py  # Multi-turn conversation via API + DB
│   └── test_evaluation_runner.py  # Full evaluation suite end-to-end
└── fixtures/
    ├── eval_dataset_small.jsonl    # Known-answer fixture for retrieval metric validation
    └── eval_reference_answers.json # Known-answer fixture for BLEU/ROUGE validation

data/
├── processed/
│   ├── train.jsonl             # Phase 1 output: 90% of Natural-Questions-Filtered.csv as ProcessedDocument JSONL
│   └── eval.jsonl              # Phase 1 output: 10% held-out split — used as the evaluation dataset
├── evaluation/
│   └── baseline_metrics.json   # Baseline metrics from first evaluation run (committed for regression tracking)
└── reports/
    └── .gitkeep                # Generated report artifacts land here (gitignored content)
```

**Structure Decision**: Extend the existing flat `src/mrag/` namespace established in Phases 1 and 2. The three new modules (`api/`, `db/`, `evaluation/`) already have empty `__init__.py` scaffolding from the Phase 0 foundation feature — this plan populates them. The API layer is the composition root for Phase 3: it constructs the Phase 2 `MRAGPipeline` at startup via the lifespan handler, injects `QueryRepository` and `EvaluationRunner` as FastAPI dependencies, and owns no retrieval or LLM logic of its own. The `evaluation/` module is importable and runnable standalone (FR-022) — the API's `POST /evaluate` is a thin wrapper over `EvaluationRunner.run_full_evaluation()`.

**Dataset lineage**: `Natural-Questions-Filtered.csv` (86,212 rows; columns: `question`, `short_answers`, `long_answers`) → Phase 1 data pipeline (`src/mrag/data/`) → `data/processed/train.jsonl` (90%) + `data/processed/eval.jsonl` (10%). The eval split is the held-out set used by the evaluation framework. Each record is a `ProcessedDocument` containing chunks with IDs that serve as ground-truth relevant passages, and `answer_short` that serves as the reference answer for BLEU/ROUGE.

## Architecture

### Data Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         HTTP Client (curl, UI, test)                    │
└─────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ FastAPI App (src/mrag/api/app.py)                                       │
│  • Lifespan: load FAISS index, LLM client, DB engine, EvaluationRunner  │
│  • Middleware: error handler → ErrorEnvelope, CORS, access logging      │
│  • Routes: /ask-question  /health  /evaluate  /analytics                │
└─────────────────────────────────────────────────────────────────────────┘
                                     │
         ┌───────────────────────────┼────────────────────────────────┐
         ▼                           ▼                                ▼
┌────────────────────┐     ┌────────────────────┐         ┌────────────────────┐
│ POST /ask-question │     │ GET /health        │         │ POST /evaluate     │
│ (ask.py)           │     │ (health.py)        │         │ (evaluate.py)      │
└────────────────────┘     └────────────────────┘         └────────────────────┘
         │                           │                                │
         ▼                           ▼                                ▼
┌────────────────────┐     ┌────────────────────┐         ┌────────────────────┐
│ MRAGPipeline.ask() │     │ HealthProbe:       │         │ EvaluationRunner   │
│ (Phase 2, unchanged│     │  • vector_store    │         │  .run_full_        │
│                    │     │  • llm_client      │         │    evaluation()    │
└────────────────────┘     │  • db_engine       │         └────────────────────┘
         │                 │  • uptime_seconds  │                    │
         ▼                 └────────────────────┘         ┌──────────┴──────────┐
┌────────────────────┐                                    ▼                     ▼
│ GeneratedResponse  │                           ┌──────────────────┐ ┌──────────────────┐
│ (query, answer,    │                           │ RetrievalMetrics │ │ ResponseQuality  │
│  confidence, srcs, │                           │ precision@K,     │ │ BLEU, ROUGE-1,   │
│  metrics)          │                           │ recall@K, MRR,   │ │ ROUGE-2, ROUGE-L │
└────────────────────┘                           │ MAP              │ └──────────────────┘
         │                                       └──────────────────┘          │
         ▼                                                │                    │
┌────────────────────┐                                    └──────────┬─────────┘
│ QueryRepository    │                                               ▼
│  .create()         │                                     ┌──────────────────┐
│  safe_persist:     │                                     │ BenchmarkResult  │
│  never blocks API  │                                     │ p50/p95/p99/qps  │
└────────────────────┘                                     └──────────────────┘
         │                                                          │
         ▼                                                          ▼
┌────────────────────┐                                     ┌──────────────────┐
│ SQLAlchemy Async   │                                     │ ReportGenerator  │
│ (SQLite/MySQL)     │                                     │ matplotlib +     │
│ QueryRecord,       │                                     │ Jinja2 HTML      │
│ ConversationTurn,  │                                     │ → single file    │
│ AnalyticsSnapshot  │                                     └──────────────────┘
└────────────────────┘                                               │
                                                                     ▼
                                                           data/reports/*.html
```

**Critical flow invariants:**

1. **API → Pipeline → DB**: The `/ask-question` route awaits `MRAGPipeline.ask()`, then hands the result to `QueryRepository.create()` wrapped in `safe_persist`. If persistence raises, the error is logged and the API still returns the in-memory `GeneratedResponse`. This is the Article VII + FR-012 guarantee.

2. **Conversation context**: When `conversation_id` is present on the request, the route loads up to `conversation_history_max_turns` turns via `ConversationRepository.get_recent_turns()`, passes them into the pipeline (the Phase 2 `QueryPipeline` already accepts a conversation history parameter), and after generation writes a new `ConversationTurn` row.

3. **Evaluation runner standalone**: `EvaluationRunner.run_full_evaluation(dataset, pipeline)` takes a pipeline instance as a parameter. It does not import from `src/mrag/api/`. The API endpoint is a thin adapter that constructs the same runner and returns its result — this satisfies FR-022 (runnable standalone).

4. **Health endpoint cheapness**: `/health` MUST return in < 1s (SC-003). LLM liveness is checked via a cached `last_successful_call_ts` updated by the pipeline on each successful generation, not by issuing a synthetic LLM call on every probe. DB liveness is a `SELECT 1`. Vector store liveness is a cached `RetrieverService.is_loaded` flag.

### Key Technical Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| HTTP framework | FastAPI 0.115.12 (already pinned) | Constitution Article VII mandate; already in `pyproject.toml` |
| ASGI server | uvicorn 0.34.2 (already pinned) | Standard FastAPI runner; already pinned |
| API app composition | Factory function + lifespan handler | Allows testability (create app per test), loads heavy resources once at startup, fails fast on missing index per FR-008 |
| Request/response validation | Pydantic v2 models in `api/schemas.py` | Article VII; existing project uses Pydantic v2 everywhere |
| Error envelope | `{"error": str, "detail": str, "status_code": int}` | Literal constitution text (Article VII) |
| OpenAPI docs | FastAPI's built-in `/docs` (Swagger UI) | Article VII mandate; zero config |
| CORS | `fastapi.middleware.cors.CORSMiddleware` with origins from `Settings.api_cors_origins` | Article VII; env-configurable allowed origins |
| ORM | SQLAlchemy 2.0 async (already pinned) | Constitution mandate |
| Async driver (SQLite) | `aiosqlite` (new dep) | Required for `sqlite+aiosqlite://` URL scheme with SQLAlchemy async engine |
| Async driver (MySQL, optional) | `aiomysql` via optional extras group | Production target per spec; extras keep default install lean |
| Schema creation | `Base.metadata.create_all()` at startup | Phase 3 scope explicitly calls migrations optional; SQLite dev DB is ephemeral, MySQL production would use a one-shot init script |
| Repository pattern | Thin repositories per entity, accepting an `AsyncSession` | Article I modularity; keeps SQLAlchemy out of routes; easy to mock in unit tests |
| Persistence isolation | `safe_persist(coro)` wrapper: try/except + structured log + swallow | FR-012 + SC-011: persistence MUST NOT block the API; failures are logged with `error=...` and `persistence_degraded=True` counter |
| Conversation context retrieval | `ConversationRepository.get_recent_turns(conversation_id, limit=N)` with `(conversation_id, turn_number DESC)` index | FR-011: up to 100 turns, preserves order, avoids full scan |
| Analytics aggregation | `SELECT COUNT/AVG/…` with indexed `created_at` + optional domain tagging | SC-005: < 1s over 100K records on SQLite/MySQL with proper indexes |
| Retrieval metrics | Custom implementations validated against `sklearn.metrics.average_precision_score` on known fixtures | Article VI + FR-021; sklearn doesn't ship precision@K directly so we compute it and assert the known-answer values |
| Response metrics — BLEU | `sacrebleu` (new dep) | Maintained, no NLTK corpus downloads, deterministic tokenization; simpler than `nltk.translate.bleu_score` |
| Response metrics — ROUGE | `rouge-score` (new dep; Google's reference implementation) | Standard ROUGE-1/2/L implementation; matches published benchmarks |
| Latency benchmarking | `time.perf_counter_ns()` + numpy percentile | Reuses Phase 2 timing primitives; percentiles via `numpy.percentile` (already a dep) |
| Report charts | `matplotlib` (new dep) | Widely supported, exports inline SVG/PNG for single-file HTML report |
| Report format | Self-contained HTML via Jinja2 template with base64-embedded PNG charts | Spec calls for "human-readable" single-file artifact; HTML renders in any browser, no PDF toolchain needed |
| Evaluation runner invocation | CLI entry + API endpoint — both call `EvaluationRunner.run_full_evaluation()` | FR-022: runnable without API process |
| Baseline comparison | JSON file at `data/evaluation/baseline_metrics.json`; per-metric regression threshold in `Settings.eval_regression_threshold` | FR-020; committed baseline enables PR-time regression gates in later work |
| Health LLM probe | Cached `last_successful_llm_call_ts` on the `GenerationPipeline`, refreshed on every successful generation | SC-003 (< 1s); avoids synthetic LLM calls on every health probe |

### New Dependencies

| Package | Version | Purpose | Notes |
|---------|---------|---------|-------|
| `aiosqlite` | ~=0.20 | Async SQLite driver for SQLAlchemy | Needed for `sqlite+aiosqlite://` URL |
| `sacrebleu` | ~=2.4 | BLEU scoring | Simpler than NLTK; no corpus downloads |
| `rouge-score` | ~=0.1 | ROUGE-1/2/L scoring | Google reference implementation |
| `matplotlib` | ~=3.9 | Chart generation for report | Inline PNG/SVG for single-file HTML |

**Already present (no change needed):** fastapi, uvicorn, sqlalchemy, scikit-learn, httpx, pydantic, structlog, Jinja2, numpy.

**Optional extras (not installed by default):**

| Package | Purpose |
|---------|---------|
| `aiomysql` | Async MySQL driver for production deployment; add under `[project.optional-dependencies].mysql` |

### Config Additions

New fields to add to `Settings` in `src/mrag/config.py`:

```python
# API
api_host: str = "0.0.0.0"
api_port: int = 8000
api_cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])
api_request_timeout_seconds: int = 30

# Database (database_url already exists)
db_pool_size: int = 5
db_pool_max_overflow: int = 10
db_echo: bool = False

# Evaluation
eval_heldout_path: str = "data/processed/eval.jsonl"
eval_baseline_path: str = "data/evaluation/baseline_metrics.json"
eval_report_dir: str = "data/reports"
eval_k_values: list[int] = Field(default_factory=lambda: [1, 3, 5, 10])
eval_benchmark_workload_size: int = 100
eval_regression_threshold: float = 0.05  # 5% drop flags a regression
```

Existing fields already cover: `database_url`, `top_k`, `llm_*`, `conversation_history_max_turns`.

## Phase 0 Outputs (research.md)

See `research.md` for resolved technical unknowns:

- **R1**: FastAPI lifespan pattern for loading heavy Phase 1/2 resources at startup
- **R2**: Async SQLAlchemy 2.0 pattern for SQLite dev / MySQL prod via same code path
- **R3**: Persistence-failure isolation strategy (`safe_persist` wrapper)
- **R4**: Retrieval metrics — validated custom implementations vs. sklearn references
- **R5**: BLEU library choice — `sacrebleu` vs. `nltk`
- **R6**: ROUGE library choice — `rouge-score` (Google) vs. alternatives
- **R7**: Self-contained HTML report strategy (matplotlib → base64 PNG → Jinja2)
- **R8**: Conversation context retrieval pattern (indexed repository query, sliding window)
- **R9**: Health endpoint cheap-probe strategy (cached timestamps vs. synthetic calls)
- **R10**: Baseline metric comparison + regression threshold semantics

## Phase 1 Outputs

- `data-model.md` — Full entity schema for API, DB, and Evaluation modules
- `contracts/api_endpoints.md` — HTTP contract for all endpoints with request/response examples
- `contracts/db_repositories.md` — Repository method signatures and transaction boundaries
- `contracts/evaluation_runner.md` — EvaluationRunner API and metric function signatures
- `quickstart.md` — Setup + verification for API service, database init, and standalone eval runs

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations. This section intentionally left empty.
