# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Multilingual RAG Platform (MRAG)** — an AI-powered Retrieval-Augmented Generation system built in three phases:

1. **Phase 1:** Dataset processing (Natural Questions dataset), multilingual embeddings (Sentence Transformers), FAISS vector store, basic retrieval
2. **Phase 2:** Query enhancement, LLM-powered response generation (Groq-compatible API), caching, performance optimization
3. **Phase 3 (Bonus):** FastAPI REST API, SQLAlchemy persistence, evaluation framework (precision@K, recall@K, BLEU, ROUGE)

## Constitution

The project constitution at `.specify/memory/constitution.md` is the supreme authority. **Read it before any specification, plan, or implementation work.** Key non-negotiable principles:

- **Modular architecture**: Every component is an independent module with explicit I/O contracts (Data Processing, Embedding, Vector Store, Query Processing, Response Generation, Caching, API, Evaluation, Database)
- **Multilingual-first**: Use multilingual embedding models (e.g., `paraphrase-multilingual-MiniLM-L12-v2`), UTF-8 throughout, no ASCII-only assumptions
- **Retrieval quality over speed**: Accuracy wins when it conflicts with performance. Raw cosine similarity alone is insufficient
- **LLM as replaceable contract**: All LLM calls go through a `BaseLLMClient` abstraction. Prompt templates externalized, never hardcoded
- **Testing is mandatory**: Unit tests per module, integration tests for full pipeline, retrieval evaluation (precision@K, recall@K, MRR), response quality (BLEU, ROUGE), latency benchmarks (p50/p95/p99)

## Tech Stack (Mandated)

| Component | Technology |
|---|---|
| Backend Framework | FastAPI (async) |
| Database ORM | SQLAlchemy (MySQL/SQLite) |
| Embeddings | Sentence Transformers (multilingual) |
| Vector Search | FAISS |
| LLM Integration | API-based, Groq-compatible interface |
| Data Processing | Pandas, NumPy |
| Evaluation | scikit-learn metrics + custom functions |
| Language | Python 3.10+ with type hints on all function signatures |
| Formatting | `black` + `ruff` or `flake8` (zero violations) |
| Logging | Structured logging (no print statements) |

## Speckit Workflow

This project uses [Speckit](https://github.com/speckit) for specification-driven development. Features are developed through a pipeline of slash commands:

1. `/speckit.specify` — Create/update feature spec from natural language description
2. `/speckit.clarify` — Ask up to 5 clarification questions on underspecified areas
3. `/speckit.plan` — Generate implementation plan with architecture and file structure
4. `/speckit.tasks` — Generate dependency-ordered tasks from the plan
5. `/speckit.checklist` — Generate custom checklist for the feature
6. `/speckit.analyze` — Cross-artifact consistency check across spec/plan/tasks
7. `/speckit.implement` — Execute all tasks from tasks.md (reads plan.md, data-model.md, contracts/, etc.)
8. `/speckit.taskstoissues` — Convert tasks to GitHub issues

Feature artifacts live under `specs/<branch-name>/` with files: `spec.md`, `plan.md`, `tasks.md`, `research.md`, `data-model.md`, `quickstart.md`, and `contracts/` directory.

Branch naming convention: `001-feature-name` or `20260319-143022-feature-name`.

## Code Standards (from Constitution)

- All configurable values (model names, chunk sizes, top-K, API URLs) must be externalized to config files or environment variables — no magic numbers
- Short-form and long-form answers require distinct processing paths
- FAISS index type selection (Flat, IVF, HNSW) must be justified by dataset size and accuracy requirements
- API error responses follow: `{"error": str, "detail": str, "status_code": int}`
- Pydantic models for all request/response validation at API boundaries
- Dependencies pinned with exact versions in `requirements.txt` or `pyproject.toml`
- Secrets via environment variables or `.env` files (gitignored)

## Dataset

**Source**: `Natural-Questions-Filtered.csv` (~86,212 rows, 3 columns)

| Column | Type | Description |
|--------|------|-------------|
| `question` | str | Natural language question (lowercase, no trailing punctuation) |
| `short_answers` | str | Concise answer (present for most records) |
| `long_answers` | str | Long-form answer / document context |

**Internal field mapping**: CSV `question` -> `RawRecord.question` -> `ProcessedDocument.question`; CSV `short_answers` -> `RawRecord.short_answers` -> `ProcessedDocument.answer_short`; CSV `long_answers` -> `RawRecord.long_answers` -> `ProcessedDocument.answer_long`

## Active Technologies
- Python 3.10+ + pydantic (v2), pydantic-settings, structlog, black, ruff, pytest, pytest-asyncio, pytest-cov, python-dotenv (001-project-foundation)
- N/A (foundation only; SQLite/MySQL deferred to Feature 008) (001-project-foundation)
- Python 3.10+ (established in Feature 000) + Pandas 2.2.3, NumPy 2.2.6, sentence-transformers 4.1.0, faiss-cpu 1.11.0, Pydantic 2.11.3, structlog 25.2.0 (002-phase1-rag-pipeline)
- FAISS index files (`.faiss`) + JSON metadata files (no database in Phase 1) (002-phase1-rag-pipeline)
- Python 3.10+ (conda environment `mrag`) + sentence-transformers 4.1.0, faiss-cpu 1.11.0, httpx 0.28.1, Jinja2, Pydantic 2.11.3, structlog 25.2.0, NumPy 2.2.6 (003-phase2-rag-pipeline)
- FAISS index files (.faiss) + JSON metadata files (no database in Phase 2) (003-phase2-rag-pipeline)
- Python 3.10+ (conda environment `mrag`) + fastapi 0.115.12, uvicorn 0.34.2, sqlalchemy 2.0.41, aiosqlite (new), scikit-learn 1.6.1, sacrebleu (new), rouge-score (new), matplotlib (new), pydantic 2.11.3, httpx 0.28.1, structlog 25.2.0 — plus existing Phase 1/2 stack (sentence-transformers 4.1.0, faiss-cpu 1.11.0, Jinja2 3.1.6) (004-phase3-rag-bonus)
- SQLite via `aiosqlite` driver for local dev; MySQL-compatible URL via `aiomysql` (optional, not installed by default) for production — same async SQLAlchemy code path; Phase 1 FAISS index (`.faiss`) + JSON metadata files remain the retrieval store (004-phase3-rag-bonus)
- TypeScript 5.4+ (strict mode, `noUncheckedIndexedAccess: true`), Node.js 20 LTS for tooling + react 18.3, react-dom 18.3, react-router-dom 6.x, vite 5.x, @vitejs/plugin-react 4.x, tailwindcss 3.x, autoprefixer, postcss, shadcn/ui primitives (radix-ui + class-variance-authority + tailwind-merge + lucide-react icons), zustand 4.x, axios 1.x, msw 2.x; dev: eslint 9.x with `@typescript-eslint`, eslint-plugin-react, eslint-plugin-react-hooks, eslint-plugin-jsx-a11y, prettier 3.x, vitest 1.x, @testing-library/react 16.x, @testing-library/jest-dom, @testing-library/user-event, jsdom, @playwright/test 1.x (wired but with no specs in this feature), @axe-core/react for automated a11y checks (005-frontend-foundation)
- Browser `localStorage` for `User Preference Set` only (selected model, top-k, score threshold, temperature, theme, schema version). No IndexedDB, no cookies, no server-side session storage. Chat state and conversation state live in-memory for the session; they are re-hydrated from the backend (Feature 004 database) in downstream chat features, not here. (005-frontend-foundation)

## Recent Changes
- 002-phase1-rag-pipeline: Fixed CSV column mapping to match actual Natural-Questions-Filtered.csv schema; load_dataset now returns (records, skipped_count); source_id is deterministic MD5 hash
- 001-project-foundation: Added Python 3.10+ + pydantic (v2), pydantic-settings, structlog, black, ruff, pytest, pytest-asyncio, pytest-cov, python-dotenv
