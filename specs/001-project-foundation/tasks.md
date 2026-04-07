# Tasks: Project Foundation & Environment Setup

**Input**: Design documents from `/specs/001-project-foundation/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: Included — spec explicitly requires unit tests for config, logging, and exceptions (SC-002, FR-008, plan.md test structure).

**Organization**: Tasks grouped by user story. US1 & US4 combined (shared files: pyproject.toml, Makefile).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4, US5)
- All paths relative to repository root

---

## Phase 1: Setup (Project Initialization)

**Purpose**: Create the three root-level project files that everything else depends on.

- [X] T001 Create pyproject.toml with project metadata (name=mrag, requires-python>=3.10), all pinned runtime dependencies (pydantic, pydantic-settings, structlog, python-dotenv, fastapi, uvicorn, sqlalchemy, sentence-transformers, faiss-cpu, pandas, numpy, scikit-learn, httpx), dev dependencies under [project.optional-dependencies.dev] (black, ruff, pytest, pytest-asyncio, pytest-cov), setuptools build backend, dynamic version from mrag.__version__, and tool config sections ([tool.ruff] with select=E,F,I,UP,B,SIM target-version=py310 line-length=88; [tool.black] line-length=88 target-version=py310; [tool.pytest.ini_options] testpaths=tests asyncio_mode=auto) in pyproject.toml
- [X] T002 [P] Create .gitignore covering Python bytecode (__pycache__, *.pyc), virtual environments (.venv, venv), environment files (.env), IDE files (.idea, .vscode, .cursor), OS files (.DS_Store), build artifacts (dist, build, *.egg-info), FAISS indices (*.faiss, *.index), model files (*.bin, *.pt), data caches, and coverage reports (.coverage, htmlcov) in .gitignore
- [X] T003 [P] Create .env.example with all 20 config fields from data-model.md documented with comments showing name, type, default value, and description — grouped by section (App, Embedding, Chunking, Retrieval, LLM, Database, Cache, Paths) in .env.example

---

## Phase 2: US1 & US4 — Project Structure & Dev Toolchain (P1/P2) :dart: MVP

**Goal**: Installable Python package with 9 importable sub-modules and single-command dev operations (install, test, lint, format).

**Independent Test**: Run `pip install -e ".[dev]"`, then `python -c "import mrag; print(mrag.__version__)"`, then `make test && make lint && make format` — all succeed with zero errors.

### Implementation

- [X] T004 [P] [US1] Create package root with `__version__ = "0.1.0"` and package-level docstring in src/mrag/__init__.py
- [X] T005 [P] [US1] Create 9 empty module sub-packages each with `__init__.py` containing module docstring in src/mrag/data/__init__.py, src/mrag/embeddings/__init__.py, src/mrag/retrieval/__init__.py, src/mrag/query/__init__.py, src/mrag/generation/__init__.py, src/mrag/cache/__init__.py, src/mrag/api/__init__.py, src/mrag/db/__init__.py, src/mrag/evaluation/__init__.py
- [X] T006 [P] [US1] Create test directory structure with shared conftest.py (fixtures for temp env overrides, temp directories, sample config dict) and __init__.py files in tests/conftest.py, tests/unit/__init__.py, tests/integration/__init__.py, tests/evaluation/__init__.py
- [X] T007 [P] [US1] Create data and prompts directory structures with .gitkeep placeholder files in data/raw/.gitkeep, data/processed/.gitkeep, data/evaluation/.gitkeep, prompts/templates/.gitkeep
- [X] T008 [US4] Create Makefile with targets: `install` (pip install -e ".[dev]"), `test` (pytest with coverage), `lint` (ruff check src/ tests/), `format` (black src/ tests/ && ruff check --fix src/ tests/), `clean` (remove __pycache__, .coverage, dist, build, *.egg-info) in Makefile
- [X] T009 [US1] Verify: run `pip install -e ".[dev]"` succeeds, `import mrag` and all 9 sub-modules importable, `mrag.__version__` returns "0.1.0", `make test && make lint && make format` pass with zero errors

**Checkpoint**: Package installs cleanly, all modules importable, dev commands functional. US1 & US4 acceptance scenarios satisfied.

---

## Phase 3: US2 — Centralized Configuration System (P1)

**Goal**: Typed, immutable config loaded from env vars / .env files with aggregate validation and SecretStr masking.

**Independent Test**: Set `LLM_API_KEY=test-key` in env, run `python -c "from mrag.config import get_settings; s = get_settings(); print(s.top_k, s.llm_api_key)"` — prints `5 **********`.

### Implementation

- [X] T010 [US2] Implement Settings(BaseSettings) class with SettingsConfigDict(frozen=True, env_file=".env", env_file_encoding="utf-8"), all 20 typed fields per data-model.md (app_name, app_version, debug, log_level, embedding_model_name, embedding_dimension, chunk_size, chunk_overlap, top_k, faiss_index_type, llm_api_url, llm_api_key as SecretStr, llm_model_name, llm_temperature, llm_max_tokens, database_url as SecretStr, cache_ttl_seconds, cache_max_size, data_dir, prompts_dir), field validators (log_level in allowed set, chunk_overlap < chunk_size, numeric bounds), and get_settings() singleton function per contracts/configuration.md in src/mrag/config.py

### Tests

- [X] T011 [US2] Write unit tests covering: .env file loading, env var override precedence, type validation (string where int expected), aggregate error reporting (multiple invalid fields in one ValidationError), immutability (frozen raises on assignment), missing .env file (still works with env vars and defaults), SecretStr masking in repr/str, get_settings() singleton behavior (same object returned), field validator constraints (chunk_overlap >= chunk_size fails, invalid log_level fails) in tests/unit/test_config.py

**Checkpoint**: Config system fully functional. Modules can `from mrag.config import get_settings` and read typed, validated settings.

---

## Phase 4: US3 — Structured Logging (P2)

**Goal**: JSON lines logging with ISO timestamps, module names, configurable levels, and automatic sensitive field redaction.

**Independent Test**: Run `python -c "from mrag.logging import configure_logging, get_logger; configure_logging('DEBUG'); log = get_logger('test'); log.info('hello', api_key='secret')"` — outputs valid JSON with `api_key: "***"`.

### Implementation

- [X] T012 [US3] Implement configure_logging(log_level: str = "INFO") configuring structlog with processor pipeline [add_log_level, TimeStamper(fmt="iso"), redact_sensitive_keys, JSONRenderer()], get_logger(name: str) returning BoundLogger with module field pre-bound, and redact_sensitive_keys processor that does case-insensitive substring matching on keys against patterns (api_key, secret, password, token, credential, database_url) replacing values with "***" per contracts/logging.md in src/mrag/logging.py

### Tests

- [X] T013 [US3] Write unit tests covering: log output is valid JSON (json.loads succeeds), required fields present (timestamp, level, module, event), ISO 8601 timestamp format, log level filtering (DEBUG not emitted at INFO level), sensitive key redaction for each pattern (api_key, secret, password, token, credential, database_url all produce "***"), non-sensitive keys pass through unchanged, multiple loggers with same name don't interfere, bound context fields appear in output in tests/unit/test_logging.py

**Checkpoint**: Logging contract fulfilled. Any module can call `get_logger(__name__)` and produce structured, redacted JSON output.

---

## Phase 5: US5 — Shared Exception Hierarchy (P3)

**Goal**: Base MRAGError with message/detail fields and 9 module-specific subclasses for uniform error handling.

**Independent Test**: Run `python -c "from mrag.exceptions import MRAGError, RetrievalError; e = RetrievalError('not found', {'index': 'missing'}); assert isinstance(e, MRAGError); print(str(e), e.detail)"` — prints `not found {'index': 'missing'}`.

### Implementation

- [X] T014 [US5] Implement MRAGError(Exception) base class with __init__(message: str, detail: dict[str, Any] | None = None), message and detail attributes, __str__ returning message, and 9 module-specific subclasses (DataProcessingError, EmbeddingError, RetrievalError, QueryProcessingError, ResponseGenerationError, CacheError, APIError, DatabaseError, EvaluationError) each inheriting from MRAGError with identical constructor per contracts/exceptions.md in src/mrag/exceptions.py

### Tests

- [X] T015 [US5] Write unit tests covering: MRAGError inherits from Exception, each of 9 subclasses inherits from MRAGError, catching MRAGError catches any subclass, str(error) returns message, detail field stores and returns dict, detail defaults to None, each subclass is independently importable from mrag.exceptions in tests/unit/test_exceptions.py

**Checkpoint**: Exception hierarchy complete. All modules can raise typed exceptions catchable via base class.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: End-to-end verification and final quality gate.

- [X] T016 Run full verification: `make install && make test && make lint && make format` — all pass with zero errors and zero warnings on the complete project (config + logging + exceptions + all tests)
- [X] T017 [P] Validate quickstart.md instructions end-to-end: follow setup steps from clean virtual environment, confirm developer can go from clone to working environment in under 5 minutes per SC-001

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **US1 & US4 (Phase 2)**: Depends on Setup (T001 must complete first; T002, T003 parallel with each other)
- **US2 (Phase 3)**: Depends on US1 (needs installed package, pyproject.toml deps)
- **US3 (Phase 4)**: Depends on US2 (reads log_level from Settings via config)
- **US5 (Phase 5)**: Depends on US1 only — **can run in parallel with US2 and US3**
- **Polish (Phase 6)**: Depends on all user stories complete

### User Story Dependencies

```
Setup (Phase 1)
  └── US1 + US4 (Phase 2)
        ├── US2 (Phase 3) ──→ US3 (Phase 4)
        └── US5 (Phase 5) [parallel with US2/US3]
              └── Polish (Phase 6)
```

- **US1 + US4 (P1/P2)**: Can start after Setup — no other story dependencies
- **US2 (P1)**: Depends on US1 — needs package installable
- **US3 (P2)**: Depends on US2 — reads log_level from Settings
- **US5 (P3)**: Depends on US1 only — independent of US2 and US3, **can be parallelized**

### Within Each User Story

- Implementation tasks before test tasks (unless TDD explicitly requested)
- Single-file stories (US2, US3, US5) are sequential within the story
- Multi-file stories (US1) have parallel opportunities marked [P]

### Parallel Opportunities

- **Phase 1**: T002 + T003 in parallel (after T001)
- **Phase 2**: T004 + T005 + T006 + T007 in parallel (then T008, then T009)
- **Cross-story**: US5 (Phase 5) can run in parallel with US2 (Phase 3) + US3 (Phase 4)
- **Phase 6**: T016 + T017 in parallel

---

## Parallel Example: Phase 2 (US1 + US4)

```bash
# Launch all structure creation tasks together:
Task: "T004 [P] [US1] Create src/mrag/__init__.py"
Task: "T005 [P] [US1] Create 9 module sub-packages"
Task: "T006 [P] [US1] Create test directory structure"
Task: "T007 [P] [US1] Create data and prompts directories"

# Then sequentially:
Task: "T008 [US4] Create Makefile"
Task: "T009 [US1] Verify installation and commands"
```

## Parallel Example: Cross-Story

```bash
# After Phase 2 completes, these can run in parallel:
# Stream A: US2 → US3 (sequential dependency)
Task: "T010 [US2] Implement Settings in src/mrag/config.py"
Task: "T011 [US2] Write config tests"
Task: "T012 [US3] Implement logging in src/mrag/logging.py"
Task: "T013 [US3] Write logging tests"

# Stream B: US5 (independent, parallel with Stream A)
Task: "T014 [US5] Implement exceptions in src/mrag/exceptions.py"
Task: "T015 [US5] Write exception tests"
```

---

## Implementation Strategy

### MVP First (US1 + US4 Only)

1. Complete Phase 1: Setup (T001-T003)
2. Complete Phase 2: US1 + US4 (T004-T009)
3. **STOP and VALIDATE**: `make install && make test && make lint && make format` passes
4. Package is installable with all modules importable — foundation ready

### Incremental Delivery

1. Setup + US1/US4 → Package scaffold ready (MVP!)
2. Add US2 → Config system operational → Test independently
3. Add US3 → Logging system operational → Test independently
4. Add US5 → Exception hierarchy complete → Test independently
5. Polish → Full verification, quickstart validation
6. Each story adds capability without breaking previous stories

### Parallel Team Strategy

With two developers after Phase 2:
- **Developer A**: US2 (config) → US3 (logging) — sequential chain
- **Developer B**: US5 (exceptions) — independent, then assists with Polish

---

## Notes

- [P] tasks = different files, no dependencies on incomplete work
- [Story] label maps task to specific user story for traceability
- US1 + US4 combined because they share pyproject.toml and Makefile — cannot be separated
- US5 is the best parallelization opportunity (independent of US2/US3)
- Commit after each completed task or logical group
- Stop at any checkpoint to validate independently
- All file paths reference plan.md project structure
