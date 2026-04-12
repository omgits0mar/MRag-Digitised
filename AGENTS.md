# MRAG Development Guidelines

Initialized from `CLAUDE.md`, the project constitution, and the current repository state. Last updated: 2026-04-12

## Project Overview

**Multilingual RAG Platform (MRAG)** is a modular Retrieval-Augmented Generation system built in phases:

1. Phase 1: dataset ingestion, preprocessing, multilingual embeddings, FAISS indexing, basic retrieval
2. Phase 2: query enhancement, LLM response generation, prompt templating, caching, performance work
3. Phase 3: FastAPI API, SQLAlchemy persistence, analytics, evaluation framework
4. Phase 4: frontend foundation and chat UX (planned; current active feature is `005-frontend-foundation`)

## Governing Documents

- Read `.specify/memory/constitution.md` before any spec, plan, or implementation work. It is the highest-authority project document.
- Use `CLAUDE.md` as the source of project-specific guidance already established for other agents.
- Keep documentation separation strict:
  - `spec.md` = what/why
  - `plan.md` = how/technical decisions
  - `tasks.md` = executable work

## Current Repository State

- The Python backend and pipeline modules already exist under `src/mrag/`.
- Implemented module areas: `data`, `embeddings`, `retrieval`, `query`, `generation`, `cache`, `api`, `db`, `evaluation`.
- Prompt templates live in `prompts/templates/`.
- Tests are already present in `tests/unit/` and `tests/integration/`.
- The primary dataset is `Natural-Questions-Filtered.csv`.
- The active spec branch is `005-frontend-foundation`, but the `frontend/` app has not been scaffolded in this repository yet.

## Active Technologies

- Python 3.10+
- FastAPI, SQLAlchemy, Pydantic v2, structlog
- Sentence Transformers, FAISS
- Pandas, NumPy
- httpx, Jinja2
- scikit-learn, sacrebleu, rouge-score, matplotlib
- pytest, pytest-asyncio, pytest-cov, black, ruff
- Planned for the active frontend feature: TypeScript 5.4+, React 18, Vite 5, Tailwind CSS, Zustand, Axios, MSW, Vitest, Playwright

## Project Structure

```text
src/mrag/
  api/           FastAPI app, routes, schemas, dependencies
  cache/         embedding/response caching, metrics, batch processing
  data/          ingestion, chunking, enrichment, export, pipeline
  db/            engine, models, repositories, schema init
  embeddings/    encoder, indexing, metadata store, pipeline
  evaluation/    datasets, metrics, benchmarks, reports, runner
  generation/    LLM client, prompt builder, validation, fallback
  query/         preprocessing, expansion, context management, pipeline
  retrieval/     retriever, ranking, retrieval models
tests/
  unit/
  integration/
specs/
  001-project-foundation/
  002-phase1-rag-pipeline/
  003-phase2-rag-pipeline/
  004-phase3-rag-bonus/
  005-frontend-foundation/
prompts/templates/
docs/
```

## Commands

Current repo commands:

- `pip install -e ".[dev]"`
- `make install`
- `make test`
- `make lint`
- `make format`
- `python -m pytest --cov=mrag --cov-report=term-missing tests/`
- `ruff check src/ tests/`
- `black src/ tests/`

Speckit workflow used in this repo:

1. `/speckit.specify`
2. `/speckit.clarify`
3. `/speckit.plan`
4. `/speckit.tasks`
5. `/speckit.checklist`
6. `/speckit.analyze`
7. `/speckit.implement`
8. `/speckit.taskstoissues`

Note: no `frontend/` package or Node-based command set exists in the repository yet. Do not assume `npm` scripts are available until that scaffold is added.

## Code Standards

- Preserve the modular architecture. Each module has explicit I/O contracts and should remain independently testable.
- Treat multilingual support as first-class: UTF-8 throughout, no ASCII-only assumptions.
- Prefer retrieval quality over speculative performance shortcuts.
- Keep LLM access behind abstractions; do not hardcode provider-specific behavior into business logic.
- Externalize configurable values to environment/configuration, not inline magic numbers.
- Use structured logging; do not introduce `print`-driven debugging into production code.
- Use type hints on all Python function signatures.
- Maintain exact dependency pinning in `pyproject.toml`.
- Add or update tests with each substantive change. Unit coverage and integration coverage are both expected.
- API errors must follow the established envelope: `{"error": str, "detail": str, "status_code": int}`.

## Working Guidance For Codex

- Check for uncommitted work before editing. The tree may be dirty; do not revert unrelated user changes.
- Use `rg` for fast codebase search.
- Prefer minimal, targeted edits that align with the existing module boundaries.
- When working on the active frontend feature, treat the current backend as an external contract and avoid inventing backend behavior that is not present in `src/mrag/api/` or the `005` spec artifacts.
- If project instructions conflict, follow this order: constitution -> direct user request -> repo reality -> `CLAUDE.md` -> feature artifacts.

## Recent Changes

- `001-project-foundation`: established config, logging, exceptions, testing, and Python project scaffolding
- `002-phase1-rag-pipeline`: added dataset processing, multilingual embeddings, FAISS indexing, retrieval, and fixed CSV column mapping to match the actual dataset
- `003-phase2-rag-pipeline`: added query enhancement, LLM generation pipeline, prompt templates, caching, and performance-oriented modules
- `004-phase3-rag-bonus`: added FastAPI routes, SQLAlchemy persistence, analytics, and evaluation metrics/reporting
- `005-frontend-foundation`: specification and plan are present; frontend implementation is not yet scaffolded

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
