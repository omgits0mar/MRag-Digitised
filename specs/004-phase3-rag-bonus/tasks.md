# Tasks: Phase 3 RAG Bonus — API Surface, Persistence & Evaluation Framework

**Input**: Design documents from `/specs/004-phase3-rag-bonus/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: Included — Article VI of the constitution mandates unit tests per module, integration tests for the full pipeline, and evaluation metric validation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add Phase 3 dependencies, config, exceptions, and test fixtures

- [x] T001 Add new dependencies (aiosqlite~=0.20, sacrebleu~=2.4, rouge-score~=0.1, matplotlib~=3.9) to pyproject.toml and run `pip install -e ".[dev]"` in the mrag conda environment
- [x] T002 [P] Add Phase 3 config fields to src/mrag/config.py: API settings (api_host, api_port, api_cors_origins, api_request_timeout_seconds), DB settings (db_pool_size, db_pool_max_overflow, db_echo), Evaluation settings (eval_heldout_path defaulting to "data/processed/eval.jsonl", eval_baseline_path, eval_report_dir, eval_k_values, eval_benchmark_workload_size, eval_regression_threshold) with validators for positive ints and threshold range — per contracts and plan.md Config Additions section
- [x] T003 [P] Add DatabaseError and EvaluationError exception classes to src/mrag/exceptions.py following the existing exception pattern in that file
- [x] T004 [P] Create test fixtures: tests/fixtures/eval_dataset_small.jsonl (10 ProcessedDocument records with known chunk IDs and answer_short for hand-computable metrics) and tests/fixtures/eval_reference_answers.json (10 generated/reference answer pairs with pre-computed BLEU and ROUGE scores)

**Checkpoint**: `pip install -e ".[dev]"` succeeds. `from mrag.config import get_settings` loads all new fields. New exception classes importable.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core DB infrastructure, API scaffolding, and evaluation models that ALL user stories depend on

**CRITICAL**: No user story work can begin until this phase is complete

- [x] T005 Create src/mrag/db/base.py with SQLAlchemy DeclarativeBase class per contracts/db_repositories.md
- [x] T006 [P] Create src/mrag/api/schemas.py with all Pydantic v2 request/response models: QuestionRequest, QuestionResponse, SourceResponse, HealthResponse, EvaluateRequest, EvaluateResponse, RegressionFlag, AnalyticsResponse, ErrorEnvelope — per data-model.md API Entities section. Include ConfigDict(from_attributes=True) where ORM conversion needed
- [x] T007 [P] Create src/mrag/evaluation/models.py with Pydantic models: EvaluationQuery, EvaluationDataset, RetrievalMetrics, ResponseQualityMetrics, BenchmarkResult, BaselineComparison, EvaluationReport — per data-model.md Evaluation Entities section
- [x] T008 Create src/mrag/db/models.py with SQLAlchemy ORM models: QueryRecord, ConversationTurn, AnalyticsSnapshot — per data-model.md Persistence Entities section. Include indexes: ix_queryrecord_created_at on created_at, ix_queryrecord_conversation_id on conversation_id, compound ix_convturn_cid_turn on (conversation_id, turn_number DESC)
- [x] T009 Create src/mrag/db/engine.py with create_db_engine() (async SQLAlchemy engine from URL), create_session_factory() (async_sessionmaker), and init_db() (idempotent Base.metadata.create_all) — per contracts/db_repositories.md. Support sqlite+aiosqlite:// and mysql+aiomysql:// URL schemes
- [x] T010 Create src/mrag/db/schema_init.py with create_tables() that calls Base.metadata.create_all via run_sync — per contracts/db_repositories.md
- [x] T011 Create src/mrag/db/utils.py with safe_persist(coro, *, operation: str) wrapper that catches all exceptions, logs via structlog, increments module-level persistence_failure_count, and never re-raises — per research.md R3 and contracts/db_repositories.md
- [x] T012 Create src/mrag/api/middleware.py with global_error_handler mapping RequestValidationError→422, DatabaseError→500, EvaluationError→500, Exception→500 to ErrorEnvelope JSON responses. Include structured access logging via structlog — per contracts/api_endpoints.md
- [x] T013 Create src/mrag/api/dependencies.py with FastAPI Depends providers: get_pipeline (from app.state), get_db_session (yield async session with commit/rollback), get_query_repo, get_conversation_repo, get_analytics_repo, get_evaluator — per contracts/api_endpoints.md
- [x] T014 Create src/mrag/api/app.py with create_app() factory and lifespan handler that loads MRAGPipeline, creates async DB engine, runs schema init, creates EvaluationRunner, registers all routes and middleware, configures CORS from settings — per research.md R1 and contracts/api_endpoints.md
- [x] T015 [P] Create tests/unit/test_db_models.py testing ORM model creation, column constraints, index definitions, and round-trip via in-memory SQLite for QueryRecord, ConversationTurn, AnalyticsSnapshot
- [x] T016 [P] Create tests/unit/test_api_schemas.py testing Pydantic validation for all request/response schemas (valid payloads pass, missing required fields reject, boundary values) and tests/unit/test_api_middleware.py testing error handler returns correct ErrorEnvelope for each exception type

**Checkpoint**: Foundation ready. `create_app()` returns a FastAPI app that starts via lifespan, creates tables, and registers middleware. All schemas and models importable. Tests pass.

---

## Phase 3: User Story 1 - Production-Ready Question Answering API (Priority: P1) MVP

**Goal**: API consumers can POST /ask-question and receive a structured answer with citations and timing

**Independent Test**: `curl -X POST http://localhost:8000/ask-question -H "Content-Type: application/json" -d '{"question":"What is photosynthesis?"}'` returns JSON with answer, confidence_score, sources, response_time_ms. Malformed payload returns 422 ErrorEnvelope.

- [x] T017 [US1] Implement POST /ask-question route in src/mrag/api/routes/ask.py: accept QuestionRequest, call MRAGPipeline.ask(), map GeneratedResponse to QuestionResponse (including SourceCitation→SourceResponse mapping), return with response_time_ms — per contracts/api_endpoints.md. Register router in app.py
- [x] T018 [US1] Create tests/integration/test_api_ask.py testing: valid question returns 200 with correct schema, empty question returns 422, malformed JSON returns 422, LLM fallback scenario returns low-confidence response — use httpx.AsyncClient with app fixture

**Checkpoint**: POST /ask-question works end-to-end. OpenAPI docs at /docs show the endpoint with examples. Tests pass.

---

## Phase 4: User Story 2 - Service Health & Readiness Visibility (Priority: P1)

**Goal**: Operators can GET /health and see status of vector store, LLM, DB, and uptime

**Independent Test**: `curl http://localhost:8000/health` returns JSON with status, vector_store, llm_provider, database, uptime_seconds, persistence_failure_count. Returns within <1 second even when dependencies degraded.

- [x] T019 [P] [US2] Implement GET /health route in src/mrag/api/routes/health.py: check RetrieverService.is_loaded flag for vector store, check GenerationPipeline last_successful_generation_ts for LLM liveness (reachable if within configurable window), execute SELECT 1 via async engine for DB, compute uptime from app.state.startup_ts, read persistence_failure_count from db/utils — per research.md R9 and contracts/api_endpoints.md. Register router in app.py
- [x] T020 [US2] Create tests/integration/test_api_health.py testing: healthy state returns all deps "loaded"/"reachable"/"connected", simulated degraded LLM returns "unreachable" with status "degraded", response always 200 and returns within 1 second

**Checkpoint**: GET /health accurately reflects dependency state. Tests pass.

---

## Phase 5: User Story 3 - Query History Persistence (Priority: P1)

**Goal**: Every question-answer exchange processed by the API is persisted with full metadata for audit

**Independent Test**: POST a question to /ask-question, then query the SQLite database and verify a QueryRecord exists with correct fields and timestamp.

- [x] T021 [US3] Implement QueryRepository class in src/mrag/db/repositories.py with create(), get_by_id(), list_by_time_range(), count_in_range(), avg_latency_in_range(), cache_hit_rate_in_range() — per contracts/db_repositories.md
- [x] T022 [P] [US3] Create tests/unit/test_db_repositories.py testing QueryRepository CRUD operations, time-range queries, and aggregation methods against in-memory SQLite
- [x] T023 [US3] Wire persistence into POST /ask-question route in src/mrag/api/routes/ask.py: after pipeline returns, call safe_persist(query_repo.create(...)) with all fields from GeneratedResponse and RequestMetrics. Persistence failure must not block the API response
- [x] T024 [US3] Create tests/integration/test_db_integration.py testing: API request creates a DB record with correct fields, second request creates second record, persistence failure (simulated) does not cause 500

**Checkpoint**: Every API request is persisted. Persistence failures are logged but don't block the caller. Tests pass.

---

## Phase 6: User Story 4 - Retrieval Quality Evaluation (Priority: P1)

**Goal**: Automated retrieval metrics (precision@K, recall@K, MRR, MAP) computed against the held-out eval split of Natural-Questions-Filtered.csv

**Independent Test**: Run evaluation on tests/fixtures/eval_dataset_small.jsonl and verify metrics match hand-computed expected values.

- [x] T025 [P] [US4] Implement dataset_loader.py in src/mrag/evaluation/dataset_loader.py: load Phase 1 eval split (data/processed/eval.jsonl), convert each ProcessedDocument to EvaluationQuery (doc_id→query_id, question→question, chunk IDs→relevant_chunk_ids, answer_short→reference_answer) — per contracts/evaluation_runner.md
- [x] T026 [P] [US4] Implement retrieval metrics in src/mrag/evaluation/retrieval_metrics.py: precision_at_k(), recall_at_k(), reciprocal_rank(), mean_reciprocal_rank(), average_precision(), mean_average_precision() — per contracts/evaluation_runner.md. All functions take predicted list[str] and relevant set[str]
- [x] T027 [US4] Create tests/unit/test_retrieval_metrics.py with known-answer test cases: perfect retrieval→precision=1.0, empty predictions→0.0, specific fixtures where hand-computed values are asserted. Validate MAP against sklearn.metrics.average_precision_score on compatible inputs — per research.md R4 and FR-021

**Checkpoint**: Retrieval metrics computable on any dataset. Known-answer tests prove correctness. Tests pass.

---

## Phase 7: User Story 5 - Response Quality Evaluation (Priority: P2)

**Goal**: Automated BLEU and ROUGE scores computed for generated answers against reference answers

**Independent Test**: Run on tests/fixtures/eval_reference_answers.json, verify identical strings→1.0, disjoint→0.0, partial overlap in between.

- [x] T028 [P] [US5] Implement response metrics in src/mrag/evaluation/response_metrics.py: compute_bleu(predictions, references)→float using sacrebleu (normalized 0–1), compute_rouge(predictions, references)→dict using rouge-score (rouge_1, rouge_2, rouge_l fmeasures) — per contracts/evaluation_runner.md and research.md R5/R6
- [x] T029 [US5] Create tests/unit/test_response_metrics.py with known-answer tests: identical text→BLEU=1.0 and ROUGE=1.0, disjoint text→0.0, partial overlap→monotonic ordering. Use fixtures from tests/fixtures/eval_reference_answers.json

**Checkpoint**: BLEU and ROUGE computable for any (prediction, reference) pair set. Tests pass.

---

## Phase 8: User Story 6 - Performance Benchmarking & Reporting (Priority: P2)

**Goal**: Repeatable latency/throughput benchmarks, baseline comparison with regression flagging, and self-contained HTML report with charts

**Independent Test**: Run benchmark on 10 queries, generate report, verify HTML file exists with precision-vs-K chart, latency histogram, and score histogram.

- [x] T030 [P] [US6] Implement latency benchmarks in src/mrag/evaluation/benchmarks.py: run_benchmark(pipeline, queries)→BenchmarkResult with p50/p95/p99 total and per-stage via numpy.percentile, plus qps throughput — per contracts/evaluation_runner.md
- [x] T031 [P] [US6] Implement baseline comparison in src/mrag/evaluation/baseline.py: load_baseline(path)→dict|None, compare_to_baseline(report, baseline, threshold_pct)→BaselineComparison with per-metric deltas and has_regressions flag, save_baseline(report, path) — per research.md R10 and contracts/evaluation_runner.md
- [x] T032 [P] [US6] Create Jinja2 HTML report template in prompts/templates/report.html.j2 with sections for retrieval metrics table, response quality table, benchmark table, three img tags for base64-embedded charts, and baseline comparison table with PASS/REGRESS indicators — per research.md R7
- [x] T033 [US6] Implement report generator in src/mrag/evaluation/report_generator.py: generate_report(report, output_dir, template_path)→str. Produce 3 matplotlib charts (precision-vs-K line, latency distribution histogram, ROUGE-L score histogram), encode as base64 PNG, render into Jinja2 template, write single self-contained HTML file — per research.md R7 and contracts/evaluation_runner.md
- [x] T034 [US6] Implement EvaluationRunner in src/mrag/evaluation/runner.py: run_full_evaluation() orchestrating dataset loading, retrieval metric computation per query, response quality computation, benchmark, baseline comparison, and report generation — per contracts/evaluation_runner.md
- [x] T035 [US6] Implement POST /evaluate route in src/mrag/api/routes/evaluate.py: accept EvaluateRequest, call EvaluationRunner.run_full_evaluation(), map EvaluationReport to EvaluateResponse — per contracts/api_endpoints.md. Register router in app.py
- [x] T036 [P] [US6] Create tests/unit/test_benchmarks.py (p50/p95/p99 on known latency arrays), tests/unit/test_baseline.py (regression flagged when delta exceeds threshold, no regression below), tests/unit/test_report_generator.py (HTML output contains expected sections and base64 img tags)
- [x] T037 [US6] Create tests/integration/test_evaluation_runner.py testing full evaluation suite end-to-end on tests/fixtures/eval_dataset_small.jsonl: all metric sections present in report, HTML report file generated, baseline comparison works
- [x] T038 [US6] Create tests/integration/test_api_evaluate.py testing POST /evaluate returns correct schema with retrieval, response_quality, benchmark sections and report_path

**Checkpoint**: Full evaluation suite runs end-to-end. HTML report produced with 3 charts. Baseline comparison flags regressions. API endpoint exposes evaluation. Tests pass.

---

## Phase 9: User Story 7 - Conversation Context Tracking (Priority: P2)

**Goal**: Multi-turn conversations tracked across API requests via conversation_id with persisted turns and context retrieval

**Independent Test**: POST two questions with the same conversation_id, verify the second response uses context from the first, and both turns are persisted with correct turn numbers.

- [x] T039 [US7] Implement ConversationRepository class in src/mrag/db/repositories.py with create_turn(conversation_id, query_text, response_text)→ConversationTurn (auto-determines turn_number) and get_recent_turns(conversation_id, limit=100)→list[ConversationTurn] in chronological order — per contracts/db_repositories.md and research.md R8
- [x] T040 [US7] Wire conversation context into POST /ask-question route in src/mrag/api/routes/ask.py: when conversation_id is present, load recent turns via ConversationRepository.get_recent_turns(), pass as conversation history to MRAGPipeline, persist new ConversationTurn after generation via safe_persist
- [x] T041 [US7] Create tests/integration/test_conversation_flow.py testing: first turn with conversation_id persists correctly, second turn resolves context, turn numbers are sequential, conversation exceeding max turns drops oldest from context

**Checkpoint**: Multi-turn conversations work through the API with persisted history. Tests pass.

---

## Phase 10: User Story 8 - Usage Analytics & Reporting (Priority: P3)

**Goal**: Aggregated usage analytics queryable via GET /analytics with total queries, avg latency, cache hit rate, and queries per day

**Independent Test**: Process 20 queries through the API, then GET /analytics and verify all aggregate fields are computed correctly.

- [x] T042 [US8] Implement AnalyticsRepository class in src/mrag/db/repositories.py with compute_analytics(start, end)→dict (total_queries, avg_latency_ms, cache_hit_rate, top_domains placeholder, queries_per_day) and save_snapshot() — per contracts/db_repositories.md. Must complete in <1s for 100K records using indexed aggregation
- [x] T043 [US8] Implement GET /analytics route in src/mrag/api/routes/analytics.py: accept optional start_date/end_date query params, call AnalyticsRepository.compute_analytics(), return AnalyticsResponse — per contracts/api_endpoints.md. Register router in app.py
- [x] T044 [US8] Create tests/integration/test_api_analytics.py testing: empty DB returns zero-valued metrics, populated DB returns correct aggregates, windowed query filters by date range

**Checkpoint**: Analytics endpoint returns correct aggregated data. Tests pass.

---

## Phase 11: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, formatting, and full suite verification

- [X] T045 Run `black` and `ruff` across all new modules (src/mrag/api/, src/mrag/db/, src/mrag/evaluation/) and fix any violations
- [X] T046 [P] Verify all new modules use structlog for logging (no print statements), all public functions have docstrings, and all function signatures have type hints
- [X] T047 Run full test suite (`make test` or `pytest tests/ -v`) and verify all tests pass including Phase 1 and Phase 2 tests (no regressions)
- [X] T048 Validate quickstart.md steps end-to-end: start server, health check, ask question, verify persistence, run evaluation, check analytics

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Stories (Phase 3–10)**: All depend on Foundational phase completion
  - See story-level dependencies below for ordering constraints
- **Polish (Phase 11)**: Depends on all user stories being complete

### User Story Dependencies

```
Setup → Foundational → US1 (ask endpoint) ──→ US3 (persistence) ──→ US7 (conversations)
                     → US2 (health) [parallel with US1]              ↘→ US8 (analytics)
                     → US4 (retrieval metrics) ──→ US6 (benchmarks + reporting + runner + /evaluate)
                     → US5 (response metrics) ──↗
```

- **US1 (P1)**: Can start after Foundational — no story dependencies
- **US2 (P1)**: Can start after Foundational — parallel with US1
- **US3 (P1)**: Depends on US1 (wires persistence into the ask route)
- **US4 (P1)**: Can start after Foundational — parallel with US1/US2 (evaluation module is independent of API)
- **US5 (P2)**: Can start after Foundational — parallel with US4
- **US6 (P2)**: Depends on US4 + US5 (runner orchestrates all metrics)
- **US7 (P2)**: Depends on US3 (builds on persistence and ask route)
- **US8 (P3)**: Depends on US3 (queries persisted records)

### Within Each User Story

- Models/entities before services/repositories
- Repositories before route wiring
- Core implementation before integration tests
- Story complete before dependent stories

### Parallel Opportunities

- **After Foundational**: US1, US2, US4, US5 can ALL start in parallel (4 parallel tracks)
- **After US1**: US3 can start
- **After US4 + US5**: US6 can start
- **After US3**: US7 and US8 can start in parallel
- **Within US6**: T030, T031, T032 are parallel (different files, no deps)
- **Within Foundational**: T006, T007, T011 are parallel; T015, T016 are parallel

---

## Parallel Example: After Foundational Completion

```
Track A: US1 (T017-T018) → US3 (T021-T024) → US7 (T039-T041) → US8 (T042-T044)
Track B: US2 (T019-T020)
Track C: US4 (T025-T027) → US6 (T030-T038)
Track D: US5 (T028-T029) ↗ (joins Track C at US6)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks all stories)
3. Complete Phase 3: US1 (POST /ask-question)
4. **STOP and VALIDATE**: `curl -X POST http://localhost:8000/ask-question -d '{"question":"What is DNA?"}'` returns a grounded answer
5. Deploy/demo if ready — this is the minimum viable API

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. US1 (ask) + US2 (health) → Functional API with health monitoring (MVP!)
3. US3 (persistence) → Every request auditable
4. US4 (retrieval metrics) + US5 (response metrics) → Quality measurable
5. US6 (benchmarks + reporting) → Full evaluation suite operational
6. US7 (conversations) → Multi-turn capability
7. US8 (analytics) → Usage insights
8. Polish → Production-ready

### Sequential Single-Developer Strategy

Complete in story priority order: Setup → Foundational → US1 → US2 → US3 → US4 → US5 → US6 → US7 → US8 → Polish

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- Constitution Article VI mandates tests for every module — tests are included
- The eval dataset is the Phase 1 eval split of Natural-Questions-Filtered.csv at data/processed/eval.jsonl
- All new modules use the conda `mrag` environment
- safe_persist (T011) is the single enforcement point for FR-012 — persistence never blocks the API
- Commit after each task or logical group
- Stop at any checkpoint to validate the story independently
