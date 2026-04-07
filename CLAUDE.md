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

## Active Technologies
- Python 3.10+ + pydantic (v2), pydantic-settings, structlog, black, ruff, pytest, pytest-asyncio, pytest-cov, python-dotenv (001-project-foundation)
- N/A (foundation only; SQLite/MySQL deferred to Feature 008) (001-project-foundation)
- Python 3.10+ (established in Feature 000) + Pandas 2.2.3, NumPy 2.2.6, sentence-transformers 4.1.0, faiss-cpu 1.11.0, Pydantic 2.11.3, structlog 25.2.0 (002-phase1-rag-pipeline)
- FAISS index files (`.faiss`) + JSON metadata files (no database in Phase 1) (002-phase1-rag-pipeline)

## Recent Changes
- 001-project-foundation: Added Python 3.10+ + pydantic (v2), pydantic-settings, structlog, black, ruff, pytest, pytest-asyncio, pytest-cov, python-dotenv
