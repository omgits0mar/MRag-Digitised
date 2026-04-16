# MRAG Project — Master Plan

**Project:** Multilingual RAG Platform (MRAG)
**Constitution Version:** 1.0.0
**Created:** 2026-04-04
**Status:** Planning
**PM:** Project Manager

---

## Project Directory Structure

```
.specify/
├── memory/
│   └── constitution.md
├── specs/
│   ├── 000-project-foundation/
│   │   ├── spec.md
│   │   ├── plan.md
│   │   └── tasks.md
│   ├── 001-dataset-processing/
│   │   ├── spec.md
│   │   ├── plan.md
│   │   └── tasks.md
│   ├── 002-embedding-vector-store/
│   │   ├── spec.md
│   │   ├── plan.md
│   │   └── tasks.md
│   ├── 003-basic-retrieval/
│   │   ├── spec.md
│   │   ├── plan.md
│   │   └── tasks.md
│   ├── 004-query-processing/
│   │   ├── spec.md
│   │   ├── plan.md
│   │   └── tasks.md
│   ├── 005-response-generation/
│   │   ├── spec.md
│   │   ├── plan.md
│   │   └── tasks.md
│   ├── 006-caching-performance/
│   │   ├── spec.md
│   │   ├── plan.md
│   │   └── tasks.md
│   ├── 007-fastapi-integration/
│   │   ├── spec.md
│   │   ├── plan.md
│   │   └── tasks.md
│   ├── 008-database-integration/
│   │   ├── spec.md
│   │   ├── plan.md
│   │   └── tasks.md
│   └── 009-evaluation-framework/
│       ├── spec.md
│       ├── plan.md
│       └── tasks.md
└── templates/
```

---

## Feature Dependency Map

```
000-project-foundation (Phase 0 — prerequisite for all)
    │
    ├── 001-dataset-processing (Phase 1)
    │       │
    │       ├── 002-embedding-vector-store (Phase 1)
    │       │       │
    │       │       └── 003-basic-retrieval (Phase 1)
    │       │               │
    │       │               ├── 004-query-processing (Phase 2)
    │       │               │       │
    │       │               │       └── 005-response-generation (Phase 2)
    │       │               │               │
    │       │               │               └── 006-caching-performance (Phase 2)
    │       │               │
    │       │               ├── 007-fastapi-integration (Phase 3 — Bonus)
    │       │               │
    │       │               ├── 008-database-integration (Phase 3 — Bonus)
    │       │               │
    │       │               └── 009-evaluation-framework (Phase 3 — Bonus)
    │
    └───────────────────────────────────────────────────────────
```

---

## Technical Context (applies to all plans)


| Field                | Value                                                            |
| -------------------- | ---------------------------------------------------------------- |
| Language/Version     | Python 3.10+                                                     |
| Primary Dependencies | FastAPI, Sentence-Transformers, FAISS, SQLAlchemy, Pandas, NumPy |
| Storage              | SQLite (dev) / MySQL (prod) via SQLAlchemy                       |
| Testing              | pytest, scikit-learn metrics, custom evaluation                  |
| Target Platform      | Linux server / local dev                                         |
| Project Type         | Library + Web Service                                            |
| Performance Goals    | <500ms p95 retrieval, <2s p95 end-to-end                         |
| Constraints          | Multilingual, API-key-driven LLM, offline-capable retrieval      |
| Scale/Scope          | ~300K Q&A pairs, single-node FAISS                               |


---

---

# FEATURE 000 — Project Foundation & Environment Setup

---

## 000 / spec.md

**Feature Branch:** 000-project-foundation
**Created:** 2026-04-04
**Status:** Draft

### Overview

Set up the complete development environment, project structure, dependency management, configuration system, and shared utilities that every subsequent feature depends on.

### User Stories

**US-000-1: As a developer, I want a standardized project structure so that all modules follow the same conventions and can be developed independently.**

- GIVEN a freshly cloned repository
- WHEN I run the setup command
- THEN all dependencies are installed, configuration loads from `.env`, and the project is ready for development
- Independent Test: Run `pytest` on an empty test suite — passes with zero errors

**US-000-2: As a developer, I want a centralized configuration system so that all settings (model names, chunk sizes, API keys) are managed in one place and never hardcoded.**

- GIVEN the application starts
- WHEN any module needs a configurable value
- THEN it reads from the configuration system which loads from environment variables or `.env` files
- Independent Test: Change a value in `.env`, restart, confirm the new value is used

**US-000-3: As a developer, I want structured logging across all modules so that I can trace operations through the entire pipeline.**

- GIVEN any module performs an operation
- WHEN the operation is logged
- THEN the log entry includes timestamp, module name, log level, and structured context
- Independent Test: Run a sample operation and verify log output matches the structured format

### Assumptions & Dependencies

- Python 3.10+ is available on all development machines
- Git is configured and the repository is initialized
- No external network dependencies at this stage (offline-capable setup)

### Constitution Compliance

- Article I: Establishes modular structure from the start
- Article IX: Sets up formatting, linting, type-hint standards
- Article IX: Configures dependency pinning and secrets management

---

## 000 / plan.md

**Branch:** 000-project-foundation | **Date:** 2026-04-04 | **Spec:** specs/000-project-foundation/spec.md
**Constitution Version:** 1.0.0

### Technical Approach

Create a Python package structure with `src/mrag/` as the root namespace. Use `pyproject.toml` for dependency management. Implement a `Settings` class using Pydantic `BaseSettings` for typed, validated configuration loading from environment variables and `.env` files. Set up `structlog` for structured JSON logging.

### Tech Stack Decisions


| Component      | Choice                      | Rationale                                        |
| -------------- | --------------------------- | ------------------------------------------------ |
| Package layout | `src/mrag/` flat namespace  | Clean imports, avoids name collisions            |
| Config         | Pydantic `BaseSettings`     | Typed validation, `.env` support, per Article IX |
| Logging        | `structlog`                 | Structured JSON output, per Article IX           |
| Formatting     | `black` + `ruff`            | Per Article IX, zero-tolerance linting           |
| Testing        | `pytest` + `pytest-asyncio` | Async support needed for FastAPI later           |
| Task runner    | `Makefile`                  | Simple, portable, no extra dependencies          |


### Project Layout

```
mrag/
├── pyproject.toml
├── Makefile
├── .env.example
├── .gitignore
├── README.md
├── src/
│   └── mrag/
│       ├── __init__.py
│       ├── config.py          # Pydantic BaseSettings
│       ├── logging.py         # structlog setup
│       ├── exceptions.py      # shared exception hierarchy
│       ├── data/              # Feature 001
│       ├── embeddings/        # Feature 002
│       ├── retrieval/         # Feature 003
│       ├── query/             # Feature 004
│       ├── generation/        # Feature 005
│       ├── cache/             # Feature 006
│       ├── api/               # Feature 007
│       ├── db/                # Feature 008
│       └── evaluation/        # Feature 009
├── tests/
│   ├── conftest.py
│   ├── unit/
│   ├── integration/
│   └── evaluation/
├── data/
│   ├── raw/
│   ├── processed/
│   └── evaluation/
├── prompts/
│   └── templates/
└── docs/
```

---

## 000 / tasks.md

**Input:** specs/000-project-foundation/
**Prerequisites:** None (foundational)

### Foundational Tasks (Phase 0)

- **T000-01** [P] — Create `pyproject.toml` with all pinned dependencies in `pyproject.toml`
  - File: `pyproject.toml`
  - Done: All dependencies resolvable, `pip install -e .` succeeds
- **T000-02** [P] — Create `.env.example` with all configurable variables documented in `.env.example`
  - File: `.env.example`
  - Done: Every config value from constitution's tech stack is listed with comments
- **T000-03** [P] — Create `.gitignore` covering Python, venvs, `.env`, FAISS indices, `__pycache__` in `.gitignore`
  - File: `.gitignore`
  - Done: No sensitive or generated files will be tracked
- **T000-04** — Create `src/mrag/config.py` with Pydantic BaseSettings class
  - File: `src/mrag/config.py`
  - Done: `Settings()` loads from env vars and `.env`, all fields have types and defaults
- **T000-05** — Create `src/mrag/logging.py` with structlog configuration
  - File: `src/mrag/logging.py`
  - Done: `get_logger(__name__)` returns structured logger with JSON output
- **T000-06** — Create `src/mrag/exceptions.py` with shared exception hierarchy
  - File: `src/mrag/exceptions.py`
  - Done: Base exception + module-specific exceptions defined
- **T000-07** — Create `src/mrag/__init__.py` with version and package metadata
  - File: `src/mrag/__init__.py`
  - Done: `import mrag; mrag.__version__` works
- **T000-08** — Create empty module directories with `__init__.py` for all 9 modules
  - Files: `src/mrag/{data,embeddings,retrieval,query,generation,cache,api,db,evaluation}/__init__.py`
  - Done: All submodules importable
- **T000-09** — Create `Makefile` with targets: install, test, lint, format, clean
  - File: `Makefile`
  - Done: `make install && make test && make lint` passes
- **T000-10** — Create `tests/conftest.py` with shared fixtures
  - File: `tests/conftest.py`
  - Done: Test fixtures for config, temp dirs, sample data accessible
- **T000-11** — Create unit tests for config and logging modules
  - Files: `tests/unit/test_config.py`, `tests/unit/test_logging.py`
  - Done: Tests pass, config loads correctly, logger produces structured output

### Checkpoint: `make install && make test && make lint` passes with zero errors.

---

---

# FEATURE 001 — Dataset Processing Pipeline

---

## 001 / spec.md

**Feature Branch:** 001-dataset-processing
**Created:** 2026-04-04
**Status:** Draft
**Depends on:** 000-project-foundation

### Overview

Download, clean, parse, chunk, and enrich the Natural Questions dataset into a structured format ready for embedding and indexing. This is the data backbone of the entire RAG system.

### User Stories

**US-001-1: As a data engineer, I want to download and parse the Natural Questions dataset so that I have clean question-answer pairs to work with.**

- GIVEN the raw dataset file (CSV/JSON)
- WHEN the ingestion pipeline runs
- THEN each record contains: question text, short answer, long answer, document context, and source metadata
- GIVEN a malformed or incomplete record
- WHEN the pipeline encounters it
- THEN it is logged as a warning and skipped without crashing the pipeline
- Independent Test: Run ingestion on a 100-row sample, verify output schema

**US-001-2: As a data engineer, I want configurable text chunking so that documents are split into retrieval-optimized segments.**

- GIVEN a long-form answer or document context
- WHEN the chunking module processes it
- THEN it produces chunks of configurable size (default 512 tokens) with configurable overlap (default 50 tokens)
- GIVEN a document shorter than the chunk size
- WHEN chunking runs
- THEN it produces a single chunk without padding
- Independent Test: Chunk a known document, verify chunk count, sizes, and overlap boundaries

**US-001-3: As a data engineer, I want automatic metadata enrichment so that each chunk carries context useful for retrieval filtering.**

- GIVEN a question-answer pair
- WHEN enrichment runs
- THEN the metadata includes: question_type (factoid/descriptive/list/yes_no), domain (auto-classified), difficulty_level (short_answer_available / long_only / no_answer), source_id, chunk_index
- Independent Test: Enrich 50 samples, verify metadata fields are populated and consistent

**US-001-4: As a data engineer, I want separate handling of short and long answers so that the system can serve different answer granularities.**

- GIVEN a record with both short and long answers
- WHEN the processing pipeline runs
- THEN two distinct answer entries are created, each linked to the original question with a type tag
- GIVEN a record with no short answer
- WHEN the pipeline runs
- THEN only the long answer is processed, and a `no_short_answer` flag is set
- Independent Test: Process mixed dataset, verify answer type distribution matches expectations

### Assumptions & Dependencies

- The Natural Questions dataset is available as CSV or can be downloaded from Kaggle
- Processing runs locally; no cloud storage dependency
- Output format is JSON Lines (`.jsonl`) for streaming compatibility

### Success Criteria

- 100% of valid records are processed without data loss
- Chunking is deterministic: same input always produces identical chunks
- Metadata enrichment covers all records with zero null required fields
- Processing pipeline can handle the full dataset (~300K records) in under 30 minutes on standard hardware

### Constitution Compliance

- Article II: Full preprocessing pipeline with validation at every boundary
- Article II: Configurable chunking with benchmarking hooks
- Article II: Separate short/long answer paths
- Article IX: Structured logging throughout pipeline
- Article X: Spec is technology-agnostic — no library names

---

## 001 / plan.md

**Branch:** 001-dataset-processing | **Date:** 2026-04-04 | **Spec:** specs/001-dataset-processing/spec.md
**Constitution Version:** 1.0.0

### Technical Approach

Build a modular data pipeline in `src/mrag/data/` with four distinct stages: ingestion, chunking, enrichment, and export. Each stage is a standalone function that takes input and produces output with validation at boundaries. Use Pandas for tabular operations and a custom `TextChunker` class for chunking logic. Metadata enrichment uses heuristic classifiers (regex + keyword matching for question type, TF-IDF for domain classification).

### Architecture

```
Raw Dataset (CSV)
    │
    ▼
[Ingestion] → validates schema, handles missing fields, normalizes text
    │
    ▼
[Chunking] → splits long text into overlapping windows, preserves sentence boundaries
    │
    ▼
[Enrichment] → classifies question type, domain, difficulty; attaches metadata
    │
    ▼
[Export] → writes .jsonl with full metadata, creates train/eval split
```

### Key Technical Decisions


| Decision                | Choice                                          | Rationale                                            |
| ----------------------- | ----------------------------------------------- | ---------------------------------------------------- |
| Chunking strategy       | Sliding window with sentence boundary alignment | Preserves semantic coherence, per Article II         |
| Chunk size              | 512 tokens default (configurable)               | Balances retrieval granularity vs. context           |
| Overlap                 | 50 tokens default (configurable)                | Ensures cross-chunk continuity                       |
| Question type detection | Regex + keyword heuristics                      | No ML dependency for classification, simple and fast |
| Domain classification   | TF-IDF + pre-defined category list              | Lightweight, no GPU required                         |
| Output format           | JSON Lines (`.jsonl`)                           | Streaming-friendly, line-by-line processing          |
| Data split              | 90% index / 10% evaluation hold-out             | Per Article VI, evaluation requires held-out data    |


### Data Model

```python
@dataclass
class ProcessedDocument:
    doc_id: str                  # unique identifier
    question: str                # original question text
    answer_short: Optional[str]  # short-form answer if available
    answer_long: str             # long-form answer / context
    chunks: List[TextChunk]      # chunked segments
    metadata: DocumentMetadata   # enrichment data

@dataclass
class TextChunk:
    chunk_id: str
    text: str
    start_pos: int
    end_pos: int
    token_count: int

@dataclass
class DocumentMetadata:
    question_type: str       # factoid | descriptive | list | yes_no
    domain: str              # science | history | geography | ...
    difficulty: str          # easy | medium | hard
    has_short_answer: bool
    source_id: str
    chunk_index: int
    total_chunks: int
```

---

## 001 / tasks.md

**Input:** specs/001-dataset-processing/
**Prerequisites:** 000-project-foundation complete

### Phase 1 — US-001-1: Dataset Ingestion

- **T001-01** — Create `src/mrag/data/ingestion.py` with dataset loading and schema validation
  - File: `src/mrag/data/ingestion.py`
  - Done: Loads CSV/JSON, validates schema, logs skipped records, returns clean DataFrame
- **T001-02** — Create `src/mrag/data/models.py` with dataclasses for ProcessedDocument, TextChunk, DocumentMetadata
  - File: `src/mrag/data/models.py`
  - Done: All data models defined with type hints and validation
- **T001-03** — Create `tests/unit/test_ingestion.py` with tests for valid, malformed, and edge-case inputs
  - File: `tests/unit/test_ingestion.py`
  - Done: Tests for valid CSV, missing columns, empty rows, encoding issues

### Phase 1 — US-001-2: Text Chunking

- **T001-04** — Create `src/mrag/data/chunking.py` with `TextChunker` class
  - File: `src/mrag/data/chunking.py`
  - Done: Configurable chunk_size, overlap; sentence boundary alignment; returns List[TextChunk]
- **T001-05** — Create `tests/unit/test_chunking.py` testing chunk sizes, overlap, edge cases
  - File: `tests/unit/test_chunking.py`
  - Done: Tests for normal text, short text, empty text, unicode text, exact boundary cases

### Phase 1 — US-001-3: Metadata Enrichment

- **T001-06** — Create `src/mrag/data/enrichment.py` with question type classifier and domain classifier
  - File: `src/mrag/data/enrichment.py`
  - Done: Classifies question_type, domain, difficulty; returns DocumentMetadata
- **T001-07** — Create `tests/unit/test_enrichment.py` with known-answer tests for each classifier
  - File: `tests/unit/test_enrichment.py`
  - Done: "Who is..." → factoid, "Explain..." → descriptive, etc.

### Phase 1 — US-001-4: Answer Handling & Export

- **T001-08** — Create `src/mrag/data/export.py` with JSONL export and train/eval splitting
  - File: `src/mrag/data/export.py`
  - Done: Writes `.jsonl`, creates 90/10 split, logs statistics
- **T001-09** — Create `src/mrag/data/pipeline.py` orchestrating ingestion → chunking → enrichment → export
  - File: `src/mrag/data/pipeline.py`
  - Done: Single `run_pipeline(config)` function chains all stages with validation
- **T001-10** — Create `tests/integration/test_data_pipeline.py` testing full pipeline on sample data
  - File: `tests/integration/test_data_pipeline.py`
  - Done: 100-row sample processes end-to-end, output validates against schema

### Checkpoint: `make test` passes. Sample dataset processed end-to-end. Output `.jsonl` validates against schema.

---

---

# FEATURE 002 — Multilingual Embeddings & Vector Store

---

## 002 / spec.md

**Feature Branch:** 002-embedding-vector-store
**Created:** 2026-04-04
**Status:** Draft
**Depends on:** 001-dataset-processing

### Overview

Generate multilingual embeddings for all processed documents and build a FAISS vector index for efficient similarity search with metadata preservation.

### User Stories

**US-002-1: As a data engineer, I want to generate multilingual embeddings for all processed chunks so that the system can perform semantic search across languages.**

- GIVEN a set of processed text chunks
- WHEN the embedding pipeline runs
- THEN each chunk has a dense vector representation generated by a multilingual model
- GIVEN text in any supported language (English, Arabic, French, Spanish, German, Chinese)
- WHEN embedded
- THEN semantically similar texts across languages produce vectors with high cosine similarity
- Independent Test: Embed "What is water?" in English and Arabic, verify cosine similarity > 0.7

**US-002-2: As a data engineer, I want a FAISS vector index so that I can perform fast approximate nearest-neighbor search on millions of vectors.**

- GIVEN a set of embedding vectors with metadata
- WHEN the indexing pipeline runs
- THEN a FAISS index is created, saved to disk, and loadable without re-computing embeddings
- GIVEN a query vector
- WHEN searching the index
- THEN the top-K most similar vectors are returned with their metadata and similarity scores
- Independent Test: Index 1000 vectors, search with a known vector, verify the correct document is in top-5

**US-002-3: As a data engineer, I want metadata preserved alongside vectors so that I can filter results by domain, question type, or other attributes.**

- GIVEN a document with metadata (domain, question_type, difficulty)
- WHEN it is indexed
- THEN the metadata is stored in a parallel lookup structure accessible by document ID
- GIVEN a search query with a metadata filter (e.g., domain="science")
- WHEN searching
- THEN only results matching the filter are returned
- Independent Test: Index mixed-domain documents, filter search by domain, verify all results match

### Assumptions & Dependencies

- Processed `.jsonl` from Feature 001 is available
- GPU is optional; embedding generation should work on CPU (slower but functional)
- FAISS index fits in memory for the target dataset size (~300K vectors)

### Success Criteria

- All chunks are embedded with the same model and dimensionality
- FAISS index loads in under 5 seconds
- Search returns results in under 100ms for K=10
- Metadata lookup by ID is O(1)

### Constitution Compliance

- Article III: Multilingual model selected from the start
- Article IV: FAISS index type justified by dataset size
- Article I: Embedding and vector store are separate modules with clear interfaces

---

## 002 / plan.md

**Branch:** 002-embedding-vector-store | **Date:** 2026-04-04 | **Spec:** specs/002-embedding-vector-store/spec.md
**Constitution Version:** 1.0.0

### Technical Approach

Use `sentence-transformers` library with `paraphrase-multilingual-MiniLM-L12-v2` (384-dimension embeddings) for multilingual support. FAISS `IndexFlatIP` (inner product on L2-normalized vectors = cosine similarity) for initial implementation; upgrade to `IndexIVFFlat` if dataset exceeds 500K vectors. Metadata stored in a separate `shelve` or JSON-backed dictionary keyed by `doc_id`.

### Key Technical Decisions


| Decision        | Choice                                   | Rationale                                                                 |
| --------------- | ---------------------------------------- | ------------------------------------------------------------------------- |
| Embedding model | `paraphrase-multilingual-MiniLM-L12-v2`  | 50+ languages, 384 dims, fast inference, per Article III                  |
| FAISS index     | `IndexFlatIP` (exact search)             | Dataset ~300K, exact search still <100ms; per Article IV accuracy > speed |
| Normalization   | L2-normalize before indexing             | Inner product on normalized vectors = cosine similarity                   |
| Metadata store  | JSON dict keyed by integer index         | O(1) lookup, serializable, no DB dependency                               |
| Batch embedding | 64-sample batches                        | Balances memory and throughput                                            |
| Persistence     | FAISS `write_index` + JSON metadata dump | Load without re-embedding                                                 |


### Module Structure

```
src/mrag/embeddings/
├── __init__.py
├── encoder.py         # EmbeddingEncoder class wrapping sentence-transformers
├── indexer.py         # FAISSIndexer class for index build/save/load/search
├── metadata_store.py  # MetadataStore class for parallel metadata
└── pipeline.py        # orchestrates: load chunks → embed → index → save
```

---

## 002 / tasks.md

**Input:** specs/002-embedding-vector-store/
**Prerequisites:** 001-dataset-processing complete

### Phase 1 — US-002-1: Embedding Generation

- **T002-01** — Create `src/mrag/embeddings/encoder.py` with `EmbeddingEncoder` class
  - File: `src/mrag/embeddings/encoder.py`
  - Done: `encode(texts: List[str]) → np.ndarray`, batched, L2-normalized, configurable model name
- **T002-02** — Create `tests/unit/test_encoder.py` testing single/batch encoding, multilingual similarity
  - File: `tests/unit/test_encoder.py`
  - Done: English-English similarity > 0.9, cross-lingual similarity > 0.6, empty input handled

### Phase 1 — US-002-2: FAISS Indexing

- **T002-03** — Create `src/mrag/embeddings/indexer.py` with `FAISSIndexer` class
  - File: `src/mrag/embeddings/indexer.py`
  - Done: `build_index()`, `search(query_vec, top_k)`, `save(path)`, `load(path)` implemented
- **T002-04** — Create `tests/unit/test_indexer.py` testing index build, search accuracy, persistence
  - File: `tests/unit/test_indexer.py`
  - Done: Known vector retrieves itself as top-1, index save/load produces identical results

### Phase 1 — US-002-3: Metadata Store

- **T002-05** — Create `src/mrag/embeddings/metadata_store.py` with `MetadataStore` class
  - File: `src/mrag/embeddings/metadata_store.py`
  - Done: `add(id, metadata)`, `get(id)`, `filter(field, value)`, `save()`, `load()` implemented
- **T002-06** — Create `tests/unit/test_metadata_store.py` testing CRUD and filtering
  - File: `tests/unit/test_metadata_store.py`
  - Done: Add/get/filter operations work correctly, persistence roundtrips

### Phase 1 — Integration

- **T002-07** — Create `src/mrag/embeddings/pipeline.py` orchestrating full embed-and-index pipeline
  - File: `src/mrag/embeddings/pipeline.py`
  - Done: Reads `.jsonl` from Feature 001, embeds, indexes, saves all artifacts
- **T002-08** — Create `tests/integration/test_embedding_pipeline.py` testing full pipeline on sample data
  - File: `tests/integration/test_embedding_pipeline.py`
  - Done: 100 chunks embedded, indexed, searchable, metadata accessible

### Checkpoint: FAISS index built. Search on 100 sample chunks returns correct top-K results.

---

---

# FEATURE 003 — Basic Retrieval System

---

## 003 / spec.md

**Feature Branch:** 003-basic-retrieval
**Created:** 2026-04-04
**Status:** Draft
**Depends on:** 002-embedding-vector-store

### Overview

Build the retrieval layer that takes a natural language query, embeds it, searches the vector store, scores and ranks results, and returns structured retrieval output.

### User Stories

**US-003-1: As a user, I want to ask a question in natural language and receive the most relevant document passages so that I can find answers to my questions.**

- GIVEN a natural language question (any supported language)
- WHEN the retrieval pipeline runs
- THEN it returns the top-K most relevant document chunks with relevance scores
- Independent Test: Ask "What is photosynthesis?", verify a biology-related chunk is in top-3

**US-003-2: As a developer, I want configurable retrieval parameters so that I can tune the system for different use cases.**

- GIVEN a retrieval request
- WHEN optional parameters are provided (top_k, score_threshold, metadata_filter)
- THEN the results respect those parameters
- Independent Test: Set top_k=3 and verify exactly 3 results; set threshold=0.5 and verify all scores ≥ 0.5

**US-003-3: As a developer, I want retrieval results to include both passage text and full metadata so that downstream components can use context for generation.**

- GIVEN a retrieval result
- WHEN examined by a downstream component
- THEN it includes: chunk_text, relevance_score, doc_id, question_type, domain, original_question, original_answer
- Independent Test: Retrieve results, verify all metadata fields are present and non-null

### Success Criteria

- Retrieval latency < 200ms for K=10 on the full dataset
- Precision@5 ≥ 0.6 on the evaluation hold-out set
- Results include complete metadata for every chunk

### Constitution Compliance

- Article IV: Configurable top-K, score thresholds, ranking algorithms
- Article IV: Retrieval metrics established as baseline
- Article I: Retrieval module is independent, consumes embedding/index as inputs

---

## 003 / plan.md

**Branch:** 003-basic-retrieval | **Date:** 2026-04-04 | **Spec:** specs/003-basic-retrieval/spec.md
**Constitution Version:** 1.0.0

### Technical Approach

Create a `RetrieverService` class that wraps embedding + FAISS search + metadata lookup into a single query interface. Results are re-ranked by a simple weighted scoring function (cosine similarity × metadata relevance). Return `RetrievalResult` dataclasses with full context.

### Module Structure

```
src/mrag/retrieval/
├── __init__.py
├── retriever.py       # RetrieverService class
├── ranking.py         # scoring and re-ranking logic
└── models.py          # RetrievalResult, RetrievalRequest dataclasses
```

---

## 003 / tasks.md

**Input:** specs/003-basic-retrieval/
**Prerequisites:** 002-embedding-vector-store complete

### Phase 1 — Retrieval Core

- **T003-01** — Create `src/mrag/retrieval/models.py` with RetrievalRequest and RetrievalResult dataclasses
  - File: `src/mrag/retrieval/models.py`
  - Done: Typed models with all fields from spec
- **T003-02** — Create `src/mrag/retrieval/ranking.py` with scoring and re-ranking functions
  - File: `src/mrag/retrieval/ranking.py`
  - Done: `rerank(results, query)` applies weighted scoring, returns sorted list
- **T003-03** — Create `src/mrag/retrieval/retriever.py` with `RetrieverService` class
  - File: `src/mrag/retrieval/retriever.py`
  - Done: `retrieve(query, top_k, threshold, filters) → List[RetrievalResult]`
- **T003-04** — Create `tests/unit/test_retriever.py` testing retrieval accuracy, parameter handling
  - File: `tests/unit/test_retriever.py`
  - Done: Tests for top-K enforcement, threshold filtering, metadata filtering, empty results
- **T003-05** — Create `tests/unit/test_ranking.py` testing re-ranking logic
  - File: `tests/unit/test_ranking.py`
  - Done: Known scores produce expected order after re-ranking
- **T003-06** — Create `tests/integration/test_retrieval_pipeline.py` end-to-end retrieval test
  - File: `tests/integration/test_retrieval_pipeline.py`
  - Done: Natural language query returns relevant results with complete metadata

### Checkpoint: End of Phase 1. Full query → embed → search → rank pipeline works. Baseline precision@5 measured.

---

---

# FEATURE 004 — Query Processing & Enhancement

---

## 004 / spec.md

**Feature Branch:** 004-query-processing
**Created:** 2026-04-04
**Status:** Draft
**Depends on:** 003-basic-retrieval

### Overview

Implement intelligent query preprocessing, normalization, expansion, and multi-turn conversation context management to improve retrieval quality.

### User Stories

**US-004-1: As a user, I want my query to be cleaned and normalized so that typos, extra whitespace, and inconsistent casing don't degrade search quality.**

- GIVEN a query with extra spaces, mixed casing, or minor typos
- WHEN preprocessing runs
- THEN the query is normalized (lowercased, whitespace-collapsed, unicode-normalized)
- Independent Test: Input "  What  IS   Photosynthesis?? " → outputs "what is photosynthesis?"

**US-004-2: As a user, I want query expansion so that my short queries still retrieve comprehensive results.**

- GIVEN a short or ambiguous query (e.g., "DNA")
- WHEN query expansion runs
- THEN additional related terms are generated (e.g., "deoxyribonucleic acid", "genetics", "double helix")
- THEN the expanded query retrieves more relevant results than the original alone
- Independent Test: Compare precision@5 for "DNA" with and without expansion

**US-004-3: As a user, I want to have multi-turn conversations so that follow-up questions use prior context.**

- GIVEN a conversation history ["What is DNA?", "How is it structured?"]
- WHEN the user asks "What about its function?"
- THEN the system resolves "it" to DNA and retrieves results about DNA function
- Independent Test: Send 3-turn conversation, verify third query retrieves DNA-function content

### Success Criteria

- Query preprocessing adds < 10ms latency
- Query expansion improves recall@10 by ≥ 10% on ambiguous queries
- Multi-turn context correctly resolves pronouns in 80%+ of test cases

### Constitution Compliance

- Article III: Unicode normalization handles multilingual input
- Article IV: Query expansion evaluated against baseline before enabling
- Article VIII: Preprocessing results cacheable

---

## 004 / plan.md

**Branch:** 004-query-processing | **Date:** 2026-04-04 | **Spec:** specs/004-query-processing/spec.md
**Constitution Version:** 1.0.0

### Technical Approach

Build a `QueryProcessor` pipeline with three stages: `normalize()`, `expand()`, `contextualize()`. Normalization uses Python's `unicodedata` and regex. Expansion uses pseudo-relevance feedback (embed query → retrieve top-3 → extract key terms → append to query). Multi-turn context uses a sliding window of conversation history prepended to the current query.

### Module Structure

```
src/mrag/query/
├── __init__.py
├── preprocessor.py      # QueryPreprocessor: normalize, clean
├── expander.py          # QueryExpander: pseudo-relevance feedback
├── context_manager.py   # ConversationContextManager: multi-turn
└── pipeline.py          # QueryPipeline orchestrating all stages
```

---

## 004 / tasks.md

**Input:** specs/004-query-processing/
**Prerequisites:** 003-basic-retrieval complete

### Phase 2 — US-004-1: Preprocessing

- **T004-01** — Create `src/mrag/query/preprocessor.py` with `QueryPreprocessor` class
  - File: `src/mrag/query/preprocessor.py`
  - Done: `normalize(query) → str` handles whitespace, casing, unicode, punctuation
- **T004-02** — Create `tests/unit/test_preprocessor.py` with edge-case tests
  - File: `tests/unit/test_preprocessor.py`
  - Done: Tests for whitespace, unicode, empty input, multilingual text

### Phase 2 — US-004-2: Query Expansion

- **T004-03** — Create `src/mrag/query/expander.py` with `QueryExpander` class
  - File: `src/mrag/query/expander.py`
  - Done: `expand(query, retriever) → ExpandedQuery` using pseudo-relevance feedback
- **T004-04** — Create `tests/unit/test_expander.py` verifying expansion adds relevant terms
  - File: `tests/unit/test_expander.py`
  - Done: Short query produces expanded version with additional terms

### Phase 2 — US-004-3: Multi-Turn Context

- **T004-05** — Create `src/mrag/query/context_manager.py` with `ConversationContextManager`
  - File: `src/mrag/query/context_manager.py`
  - Done: `add_turn(query, response)`, `get_contextualized_query(new_query) → str`
- **T004-06** — Create `tests/unit/test_context_manager.py` testing pronoun resolution and history
  - File: `tests/unit/test_context_manager.py`
  - Done: Multi-turn scenarios with pronoun resolution verified

### Phase 2 — Integration

- **T004-07** — Create `src/mrag/query/pipeline.py` chaining preprocessor → expander → contextualizer
  - File: `src/mrag/query/pipeline.py`
  - Done: `process(query, history) → ProcessedQuery` produces enhanced query for retrieval
- **T004-08** — Create `tests/integration/test_query_pipeline.py` testing full query pipeline
  - File: `tests/integration/test_query_pipeline.py`
  - Done: Raw input processed through all stages, output improves retrieval vs. raw query

### Checkpoint: Query processing pipeline operational. Expansion improves recall@10 on test set.

---

---

# FEATURE 005 — LLM Response Generation

---

## 005 / spec.md

**Feature Branch:** 005-response-generation
**Created:** 2026-04-04
**Status:** Draft
**Depends on:** 004-query-processing, 003-basic-retrieval

### Overview

Integrate with an LLM API to generate natural language answers grounded in retrieved context, with quality filtering, confidence scoring, and fallback mechanisms.

### User Stories

**US-005-1: As a user, I want natural language answers generated from retrieved passages so that I get direct answers instead of raw document chunks.**

- GIVEN a question and retrieved context passages
- WHEN the generation pipeline runs
- THEN a coherent, grounded answer is generated that cites the retrieved passages
- Independent Test: Ask a factual question, verify the answer is derived from the retrieved context

**US-005-2: As a user, I want the system to tell me when it doesn't know the answer so that I can trust the responses I receive.**

- GIVEN a question with no relevant context retrieved (all scores below threshold)
- WHEN the generation pipeline runs
- THEN the system returns a "I don't have enough information to answer this question" response with a low confidence score
- Independent Test: Ask an out-of-domain question, verify fallback response

**US-005-3: As a developer, I want prompt templates to be externalized and versioned so that I can iterate on prompt engineering without code changes.**

- GIVEN a prompt template file
- WHEN the generation pipeline loads
- THEN it reads the template from the file system, not from hardcoded strings
- GIVEN a template is updated
- WHEN the next query runs
- THEN the updated template is used without restarting the service
- Independent Test: Change a template file, run a query, verify the new template is reflected

**US-005-4: As a developer, I want response quality validation so that low-quality or hallucinated answers are filtered before reaching the user.**

- GIVEN a generated response
- WHEN quality validation runs
- THEN a confidence score is computed based on retrieval relevance and answer grounding
- GIVEN a response that contradicts the retrieved context
- WHEN validation detects the contradiction
- THEN the response is flagged and the fallback mechanism is triggered
- Independent Test: Generate a response from weak context, verify confidence score is below threshold

### Success Criteria

- Generated answers are grounded in retrieved context (no hallucination in 90%+ of cases)
- Fallback triggers correctly for out-of-domain questions
- Prompt template changes take effect without service restart
- End-to-end latency (retrieval + generation) < 3 seconds p95

### Constitution Compliance

- Article V: LLM behind abstraction interface, no provider lock-in
- Article V: Externalized prompt templates
- Article V: Fallback for low-confidence answers
- Article V: Environment-variable-driven API keys

---

## 005 / plan.md

**Branch:** 005-response-generation | **Date:** 2026-04-04 | **Spec:** specs/005-response-generation/spec.md
**Constitution Version:** 1.0.0

### Technical Approach

Create a `BaseLLMClient` abstract class with a `GroqLLMClient` concrete implementation. Build a `PromptBuilder` that loads Jinja2 templates from the `prompts/templates/` directory. Implement `ResponseValidator` with confidence scoring based on retrieval score aggregation and answer-context overlap. Fallback returns a canned response when confidence < configurable threshold.

### Module Structure

```
src/mrag/generation/
├── __init__.py
├── llm_client.py        # BaseLLMClient ABC + GroqLLMClient
├── prompt_builder.py    # PromptBuilder loading Jinja2 templates
├── validator.py         # ResponseValidator with confidence scoring
├── fallback.py          # FallbackHandler for low-confidence responses
└── pipeline.py          # GenerationPipeline orchestrating all stages

prompts/templates/
├── qa_prompt.j2         # Main Q&A prompt template
├── system_prompt.j2     # System instruction template
└── fallback_prompt.j2   # Fallback response template
```

### Key Technical Decisions


| Decision             | Choice                                                               | Rationale                                   |
| -------------------- | -------------------------------------------------------------------- | ------------------------------------------- |
| LLM abstraction      | ABC `BaseLLMClient`                                                  | Per Article V, swappable providers          |
| Prompt templating    | Jinja2 from filesystem                                               | Per Article V, externalized, hot-reloadable |
| Confidence scoring   | Weighted average of retrieval scores + answer-context TF-IDF overlap | Simple, no extra model needed               |
| Confidence threshold | 0.3 default (configurable)                                           | Calibrated on evaluation set                |
| Fallback strategy    | Canned response + log                                                | Honest uncertainty per Article V            |


---

## 005 / tasks.md

**Input:** specs/005-response-generation/
**Prerequisites:** 003-basic-retrieval, 004-query-processing complete

### Phase 2 — US-005-1 & US-005-3: LLM Client & Prompt Templates

- **T005-01** — Create `src/mrag/generation/llm_client.py` with `BaseLLMClient` ABC and `GroqLLMClient`
  - File: `src/mrag/generation/llm_client.py`
  - Done: `generate(prompt, **kwargs) → str` async method, API key from env, error handling
- **T005-02** — Create `src/mrag/generation/prompt_builder.py` with `PromptBuilder` class
  - File: `src/mrag/generation/prompt_builder.py`
  - Done: `build_prompt(query, context_chunks, history) → str` using Jinja2 templates
- **T005-03** — Create prompt template files in `prompts/templates/`
  - Files: `prompts/templates/qa_prompt.j2`, `system_prompt.j2`, `fallback_prompt.j2`
  - Done: Templates include context injection, citation formatting, conversation history
- **T005-04** — Create `tests/unit/test_llm_client.py` with mocked API tests
  - File: `tests/unit/test_llm_client.py`
  - Done: Mocked responses, error handling, timeout handling tested
- **T005-05** — Create `tests/unit/test_prompt_builder.py` testing template rendering
  - File: `tests/unit/test_prompt_builder.py`
  - Done: Templates render correctly with various inputs, missing fields handled

### Phase 2 — US-005-2 & US-005-4: Validation & Fallback

- **T005-06** — Create `src/mrag/generation/validator.py` with `ResponseValidator` class
  - File: `src/mrag/generation/validator.py`
  - Done: `validate(response, context, scores) → ValidationResult` with confidence score
- **T005-07** — Create `src/mrag/generation/fallback.py` with `FallbackHandler` class
  - File: `src/mrag/generation/fallback.py`
  - Done: Returns fallback response when confidence < threshold
- **T005-08** — Create `tests/unit/test_validator.py` testing confidence scoring
  - File: `tests/unit/test_validator.py`
  - Done: High-relevance context → high confidence, no context → low confidence

### Phase 2 — Integration

- **T005-09** — Create `src/mrag/generation/pipeline.py` orchestrating full generation pipeline
  - File: `src/mrag/generation/pipeline.py`
  - Done: `generate_answer(query, retrieval_results, history) → GeneratedResponse`
- **T005-10** — Create `tests/integration/test_generation_pipeline.py` testing end-to-end
  - File: `tests/integration/test_generation_pipeline.py`
  - Done: Query → retrieval → generation → validation → response tested

### Checkpoint: End-to-end Q&A pipeline works. Fallback triggers correctly. Templates are hot-reloadable.

---

---

# FEATURE 006 — Caching & Performance Optimization

---

## 006 / spec.md

**Feature Branch:** 006-caching-performance
**Created:** 2026-04-04
**Status:** Draft
**Depends on:** 005-response-generation

### Overview

Implement intelligent caching for embeddings and search results, batch processing for bulk operations, and performance metrics collection on every request.

### User Stories

**US-006-1: As a system operator, I want query results cached so that repeated or similar questions are served instantly.**

- GIVEN a query that was previously answered
- WHEN the same or near-identical query arrives
- THEN the cached result is returned without re-embedding, re-searching, or re-generating
- Independent Test: Send the same query twice, verify the second response time is <50ms

**US-006-2: As a data engineer, I want batch processing so that I can re-index the entire dataset or run evaluation on thousands of queries efficiently.**

- GIVEN a list of 1000 queries
- WHEN batch processing runs
- THEN all queries are processed with optimized batched embedding and search, not sequentially
- Independent Test: Batch-process 100 queries, verify throughput is ≥ 3x single-query throughput

**US-006-3: As a system operator, I want performance metrics collected on every request so that I can monitor system health and identify bottlenecks.**

- GIVEN any query processed by the system
- WHEN the request completes
- THEN metrics are recorded: embedding_time_ms, search_time_ms, llm_time_ms, total_time_ms, cache_hit (bool)
- Independent Test: Process 10 queries, verify all metric fields are populated in the metrics store

### Success Criteria

- Cache hit rate > 50% under normal usage patterns
- Batch processing throughput ≥ 50 queries/second for retrieval-only workloads
- Metrics collection adds < 5ms overhead per request

### Constitution Compliance

- Article VIII: LRU/TTL caching with explicit invalidation
- Article VIII: Batch processing for bulk operations
- Article VIII: Metrics collected on every request
- Article VIII: Memory usage monitored

---

## 006 / plan.md

**Branch:** 006-caching-performance | **Date:** 2026-04-04 | **Spec:** specs/006-caching-performance/spec.md
**Constitution Version:** 1.0.0

### Technical Approach

Implement a two-level cache: L1 (in-memory LRU for embeddings) and L2 (TTL-based dict for full responses keyed by query hash). Batch processing uses the existing encoder's batch capabilities with configurable batch sizes. Metrics collected via a `MetricsCollector` singleton using Python's `time.perf_counter_ns()` with export to JSON logs.

### Module Structure

```
src/mrag/cache/
├── __init__.py
├── embedding_cache.py   # LRU cache for query embeddings
├── response_cache.py    # TTL cache for full responses
├── batch_processor.py   # Batch query processing
└── metrics.py           # MetricsCollector for performance tracking
```

---

## 006 / tasks.md

**Input:** specs/006-caching-performance/
**Prerequisites:** 005-response-generation complete

### Phase 2 — Caching & Batch & Metrics

- **T006-01** — Create `src/mrag/cache/embedding_cache.py` with LRU cache for embeddings
  - File: `src/mrag/cache/embedding_cache.py`
  - Done: LRU cache with configurable max size, `get(key)`, `put(key, vec)`, `invalidate(key)`
- **T006-02** — Create `src/mrag/cache/response_cache.py` with TTL cache for responses
  - File: `src/mrag/cache/response_cache.py`
  - Done: TTL-based cache, `get(query_hash)`, `put(query_hash, response, ttl)`, auto-expiration
- **T006-03** — Create `src/mrag/cache/batch_processor.py` with `BatchProcessor` class
  - File: `src/mrag/cache/batch_processor.py`
  - Done: `process_batch(queries) → List[Response]` with batched embedding and search
- **T006-04** — Create `src/mrag/cache/metrics.py` with `MetricsCollector` class
  - File: `src/mrag/cache/metrics.py`
  - Done: `start_timer(label)`, `stop_timer(label)`, `record(request_metrics)`, `export() → dict`
- **T006-05** — Create `tests/unit/test_caching.py` testing LRU and TTL caches
  - File: `tests/unit/test_caching.py`
  - Done: Cache hits, misses, eviction, TTL expiration, invalidation tested
- **T006-06** — Create `tests/unit/test_batch_processor.py` testing batch throughput
  - File: `tests/unit/test_batch_processor.py`
  - Done: Batch of 100 queries processed, throughput measured, results correct
- **T006-07** — Create `tests/unit/test_metrics.py` testing metrics collection
  - File: `tests/unit/test_metrics.py`
  - Done: Metrics recorded and exported correctly for sample requests
- **T006-08** — Integrate caching and metrics into existing retrieval and generation pipelines
  - Files: Update `src/mrag/retrieval/retriever.py`, `src/mrag/generation/pipeline.py`
  - Done: Cache consulted before compute, metrics collected on every request

### Checkpoint: End of Phase 2. Full pipeline with caching, batch processing, and metrics. Phase 2 exit criteria met.

---

---

# FEATURE 007 — FastAPI Integration (Phase 3 — Bonus)

---

## 007 / spec.md

**Feature Branch:** 007-fastapi-integration
**Created:** 2026-04-04
**Status:** Draft
**Depends on:** 006-caching-performance

### Overview

Build production-ready REST API endpoints that expose the RAG system's capabilities with proper validation, error handling, and documentation.

### User Stories

**US-007-1: As an API consumer, I want a POST /ask-question endpoint so that I can submit questions and receive AI-generated answers.**

- GIVEN a valid JSON request with a question field
- WHEN I POST to /ask-question
- THEN I receive a JSON response with: answer, confidence_score, sources (list of cited passages), response_time_ms
- GIVEN an empty or malformed request
- WHEN I POST to /ask-question
- THEN I receive a 422 error with descriptive validation messages
- Independent Test: POST a question via curl, verify response schema

**US-007-2: As a system operator, I want a GET /health endpoint so that I can monitor system liveness and dependency status.**

- GIVEN the system is running
- WHEN I GET /health
- THEN I receive status of: vector_store (loaded/not_loaded), llm_provider (reachable/unreachable), database (connected/disconnected), uptime_seconds
- Independent Test: GET /health, verify all dependency statuses are reported

**US-007-3: As a developer, I want a POST /evaluate endpoint so that I can trigger evaluation runs and retrieve metrics.**

- GIVEN a valid evaluation request with an optional dataset_path
- WHEN I POST to /evaluate
- THEN the evaluation suite runs and returns: precision_at_k, recall_at_k, avg_latency_ms, total_queries
- Independent Test: POST /evaluate with test dataset, verify metrics are returned

### Success Criteria

- All endpoints return correct HTTP status codes (200, 422, 500)
- OpenAPI docs available at `/docs`
- Response times meet p95 targets from constitution
- CORS configured for allowed origins

### Constitution Compliance

- Article VII: FastAPI with async, Pydantic models, consistent error schema
- Article VII: Health check reports dependency status
- Article VII: OpenAPI documentation with examples

---

## 007 / plan.md

**Branch:** 007-fastapi-integration | **Date:** 2026-04-04 | **Spec:** specs/007-fastapi-integration/spec.md
**Constitution Version:** 1.0.0

### Technical Approach

FastAPI application with async endpoints. Pydantic `BaseModel` for all request/response schemas. Dependency injection for services (retriever, generator, evaluator). CORS middleware configured. Lifespan handler loads FAISS index and models at startup.

### Module Structure

```
src/mrag/api/
├── __init__.py
├── app.py             # FastAPI app factory with lifespan
├── routes/
│   ├── __init__.py
│   ├── ask.py         # POST /ask-question
│   ├── health.py      # GET /health
│   └── evaluate.py    # POST /evaluate
├── schemas.py         # Pydantic request/response models
├── dependencies.py    # Dependency injection for services
└── middleware.py       # Error handling, CORS, logging
```

---

## 007 / tasks.md

**Input:** specs/007-fastapi-integration/
**Prerequisites:** 006-caching-performance complete

### Phase 3 — API Endpoints

- **T007-01** — Create `src/mrag/api/schemas.py` with Pydantic request/response models
  - File: `src/mrag/api/schemas.py`
  - Done: `QuestionRequest`, `QuestionResponse`, `HealthResponse`, `EvaluateRequest`, `EvaluateResponse`, `ErrorResponse`
- **T007-02** — Create `src/mrag/api/dependencies.py` with dependency injection
  - File: `src/mrag/api/dependencies.py`
  - Done: `get_retriever()`, `get_generator()`, `get_evaluator()` dependency providers
- **T007-03** — Create `src/mrag/api/routes/ask.py` with POST /ask-question endpoint
  - File: `src/mrag/api/routes/ask.py`
  - Done: Async endpoint, uses retriever + generator, returns structured response
- **T007-04** — Create `src/mrag/api/routes/health.py` with GET /health endpoint
  - File: `src/mrag/api/routes/health.py`
  - Done: Reports vector_store, llm_provider, database status
- **T007-05** — Create `src/mrag/api/routes/evaluate.py` with POST /evaluate endpoint
  - File: `src/mrag/api/routes/evaluate.py`
  - Done: Triggers evaluation, returns metrics
- **T007-06** — Create `src/mrag/api/middleware.py` with error handling and CORS
  - File: `src/mrag/api/middleware.py`
  - Done: Global error handler returns consistent error schema, CORS configured
- **T007-07** — Create `src/mrag/api/app.py` with FastAPI app factory and lifespan
  - File: `src/mrag/api/app.py`
  - Done: App loads models on startup, registers routes, middleware, OpenAPI docs at /docs
- **T007-08** — Create `tests/integration/test_api.py` testing all endpoints with TestClient
  - File: `tests/integration/test_api.py`
  - Done: All three endpoints tested for success and error cases

### Checkpoint: All API endpoints functional. OpenAPI docs accessible. Error handling consistent.

---

---

# FEATURE 008 — Database Integration (Phase 3 — Bonus)

---

## 008 / spec.md

**Feature Branch:** 008-database-integration
**Created:** 2026-04-04
**Status:** Draft
**Depends on:** 007-fastapi-integration

### Overview

Set up persistent storage for query history, responses, conversation tracking, and analytics using SQLAlchemy.

### User Stories

**US-008-1: As a system operator, I want all queries and responses persisted so that I can analyze usage patterns and system performance over time.**

- GIVEN a query is processed by the system
- WHEN the response is returned
- THEN the query text, response text, confidence score, latency metrics, and timestamp are saved to the database
- Independent Test: Process a query via API, check database has a new record

**US-008-2: As a user, I want conversation context tracked across requests so that follow-up questions work without me re-sending history.**

- GIVEN a conversation_id in my request
- WHEN I send a follow-up question
- THEN the system retrieves prior turns from the database and uses them for context
- Independent Test: Send two requests with the same conversation_id, verify second uses first's context

**US-008-3: As a system operator, I want query analytics aggregated so that I can generate reports on usage, performance, and common topics.**

- GIVEN accumulated query data
- WHEN I request analytics
- THEN the system returns: total_queries, avg_latency, cache_hit_rate, top_domains, queries_per_day
- Independent Test: Process 20 queries, request analytics, verify all metrics are computed

### Success Criteria

- Database operations add < 50ms latency to requests
- Conversation history retrieval supports up to 100 turns
- Analytics queries complete in < 1 second for up to 100K records

### Constitution Compliance

- Article VII: SQLAlchemy with SQLite/MySQL support
- Article IX: Database credentials via environment variables
- Article I: Database module independent from retrieval/generation modules

---

## 008 / plan.md

**Branch:** 008-database-integration | **Date:** 2026-04-04 | **Spec:** specs/008-database-integration/spec.md
**Constitution Version:** 1.0.0

### Technical Approach

SQLAlchemy ORM with async session support (`asyncio` extension). Models for `QueryRecord`, `ConversationTurn`, and `AnalyticsSnapshot`. SQLite for development, MySQL connection string configurable via environment. Repository pattern for data access.

### Module Structure

```
src/mrag/db/
├── __init__.py
├── engine.py          # async engine and session factory
├── models.py          # SQLAlchemy ORM models
├── repositories.py    # QueryRepository, ConversationRepository, AnalyticsRepository
└── migrations/        # Alembic migrations (optional)
```

### Data Model

```
QueryRecord:
  id (PK), query_text, response_text, confidence_score,
  embedding_time_ms, search_time_ms, llm_time_ms, total_time_ms,
  cache_hit, conversation_id (FK), created_at

ConversationTurn:
  id (PK), conversation_id (indexed), turn_number,
  query_text, response_text, created_at

AnalyticsSnapshot:
  id (PK), period_start, period_end, total_queries,
  avg_latency_ms, cache_hit_rate, top_domains_json, created_at
```

---

## 008 / tasks.md

**Input:** specs/008-database-integration/
**Prerequisites:** 007-fastapi-integration complete

### Phase 3 — Database

- **T008-01** — Create `src/mrag/db/engine.py` with async SQLAlchemy engine and session factory
  - File: `src/mrag/db/engine.py`
  - Done: `get_engine()`, `get_session()`, DB URL from config
- **T008-02** — Create `src/mrag/db/models.py` with SQLAlchemy ORM models
  - File: `src/mrag/db/models.py`
  - Done: `QueryRecord`, `ConversationTurn`, `AnalyticsSnapshot` models defined
- **T008-03** — Create `src/mrag/db/repositories.py` with repository classes
  - File: `src/mrag/db/repositories.py`
  - Done: CRUD operations for all models, analytics aggregation queries
- **T008-04** — Integrate database persistence into API endpoints
  - Files: Update `src/mrag/api/routes/ask.py`, `src/mrag/api/dependencies.py`
  - Done: Every API request persists to database, conversation_id supported
- **T008-05** — Create `tests/unit/test_db_models.py` testing ORM models
  - File: `tests/unit/test_db_models.py`
  - Done: Models create/read/update/delete correctly with in-memory SQLite
- **T008-06** — Create `tests/integration/test_db_integration.py` testing API + DB flow
  - File: `tests/integration/test_db_integration.py`
  - Done: API request → DB record created → query analytics computed

### Checkpoint: All queries persisted. Conversations trackable. Analytics queryable.

---

---

# FEATURE 009 — Evaluation Framework (Phase 3 — Bonus)

---

## 009 / spec.md

**Feature Branch:** 009-evaluation-framework
**Created:** 2026-04-04
**Status:** Draft
**Depends on:** 003-basic-retrieval, 005-response-generation

### Overview

Build a comprehensive evaluation framework measuring retrieval accuracy, response quality, latency benchmarks, and generating performance reports.

### User Stories

**US-009-1: As a developer, I want retrieval accuracy metrics computed automatically so that I can measure how well the system finds relevant passages.**

- GIVEN a held-out evaluation dataset with known relevant passages
- WHEN the retrieval evaluation runs
- THEN precision@K, recall@K, MRR, and MAP are computed for K=1,3,5,10
- Independent Test: Run evaluation on 100 test queries, verify all metrics are computed

**US-009-2: As a developer, I want response quality metrics so that I can measure how good the generated answers are.**

- GIVEN generated answers and ground-truth answers
- WHEN quality evaluation runs
- THEN BLEU, ROUGE-1, ROUGE-2, and ROUGE-L scores are computed
- Independent Test: Evaluate 50 generated answers, verify all scores are in [0, 1]

**US-009-3: As a developer, I want performance benchmarks so that I can track latency and throughput over time.**

- GIVEN a benchmark workload (100 queries)
- WHEN the benchmark runs
- THEN p50, p95, p99 latency and queries/second throughput are reported
- Independent Test: Run benchmark, verify all metrics are present in the report

**US-009-4: As a system operator, I want evaluation reports as visualizations so that I can present results to stakeholders.**

- GIVEN computed evaluation metrics
- WHEN report generation runs
- THEN a report with charts (precision vs. K, latency distribution, score histograms) is produced
- Independent Test: Generate report, verify output file exists and contains expected charts

### Success Criteria

- Evaluation suite runs end-to-end on the held-out dataset
- All metrics are computed correctly (validated against scikit-learn reference implementations)
- Reports are generated as HTML or PDF with embedded charts

### Constitution Compliance

- Article VI: Precision@K, Recall@K, BLEU, ROUGE, latency benchmarks
- Article VI: Evaluation on held-out set
- Article VI: Regression testing via comparison with baseline metrics
- Article IV: Retrieval changes validated against metrics before merging

---

## 009 / plan.md

**Branch:** 009-evaluation-framework | **Date:** 2026-04-04 | **Spec:** specs/009-evaluation-framework/spec.md
**Constitution Version:** 1.0.0

### Technical Approach

Use scikit-learn for precision/recall/MRR. Use `rouge-score` library for ROUGE metrics. Use `nltk` for BLEU. Custom latency benchmarking with `time.perf_counter_ns()`. Reports generated with `matplotlib` and exported as HTML via Jinja2 templates.

### Module Structure

```
src/mrag/evaluation/
├── __init__.py
├── retrieval_metrics.py    # precision@K, recall@K, MRR, MAP
├── response_metrics.py     # BLEU, ROUGE scores
├── benchmarks.py           # latency and throughput benchmarking
├── report_generator.py     # visualization and report export
└── runner.py               # EvaluationRunner orchestrating all evaluations
```

---

## 009 / tasks.md

**Input:** specs/009-evaluation-framework/
**Prerequisites:** 003-basic-retrieval, 005-response-generation complete

### Phase 3 — Evaluation

- **T009-01** — Create `src/mrag/evaluation/retrieval_metrics.py` with precision@K, recall@K, MRR, MAP
  - File: `src/mrag/evaluation/retrieval_metrics.py`
  - Done: Functions take predicted/relevant sets, return float scores
- **T009-02** — Create `src/mrag/evaluation/response_metrics.py` with BLEU and ROUGE
  - File: `src/mrag/evaluation/response_metrics.py`
  - Done: `compute_bleu(predicted, reference)`, `compute_rouge(predicted, reference)` return dicts
- **T009-03** — Create `src/mrag/evaluation/benchmarks.py` with latency/throughput benchmarking
  - File: `src/mrag/evaluation/benchmarks.py`
  - Done: `run_benchmark(queries, pipeline) → BenchmarkResult` with p50/p95/p99/qps
- **T009-04** — Create `src/mrag/evaluation/report_generator.py` with visualization and export
  - File: `src/mrag/evaluation/report_generator.py`
  - Done: Generates HTML report with matplotlib charts
- **T009-05** — Create `src/mrag/evaluation/runner.py` orchestrating full evaluation suite
  - File: `src/mrag/evaluation/runner.py`
  - Done: `run_full_evaluation(eval_dataset, pipeline) → EvaluationReport`
- **T009-06** — Create `tests/unit/test_retrieval_metrics.py` with known-answer metric tests
  - File: `tests/unit/test_retrieval_metrics.py`
  - Done: Metrics match scikit-learn reference implementations for known inputs
- **T009-07** — Create `tests/unit/test_response_metrics.py` with known-answer BLEU/ROUGE tests
  - File: `tests/unit/test_response_metrics.py`
  - Done: Perfect match → score 1.0, no overlap → score 0.0
- **T009-08** — Create `tests/integration/test_evaluation_runner.py` testing full evaluation
  - File: `tests/integration/test_evaluation_runner.py`
  - Done: Full evaluation runs on sample data, report generated, all metrics present

### Checkpoint: End of Phase 3. Full evaluation suite operational. Report generated with all metrics. Project complete.

---

---

# MASTER TASK SUMMARY

## Total: 10 Features, 80 Tasks


| Feature                        | Phase     | Tasks                        | Dependencies | Status        |
| ------------------------------ | --------- | ---------------------------- | ------------ | ------------- |
| 000 — Project Foundation       | 0         | T000-01 → T000-11 (11 tasks) | None         | ⬜ Not Started |
| 001 — Dataset Processing       | 1         | T001-01 → T001-10 (10 tasks) | 000          | ⬜ Not Started |
| 002 — Embedding & Vector Store | 1         | T002-01 → T002-08 (8 tasks)  | 001          | ⬜ Not Started |
| 003 — Basic Retrieval          | 1         | T003-01 → T003-06 (6 tasks)  | 002          | ⬜ Not Started |
| 004 — Query Processing         | 2         | T004-01 → T004-08 (8 tasks)  | 003          | ⬜ Not Started |
| 005 — Response Generation      | 2         | T005-01 → T005-10 (10 tasks) | 003, 004     | ⬜ Not Started |
| 006 — Caching & Performance    | 2         | T006-01 → T006-08 (8 tasks)  | 005          | ⬜ Not Started |
| 007 — FastAPI Integration      | 3 (Bonus) | T007-01 → T007-08 (8 tasks)  | 006          | ⬜ Not Started |
| 008 — Database Integration     | 3 (Bonus) | T008-01 → T008-06 (6 tasks)  | 007          | ⬜ Not Started |
| 009 — Evaluation Framework     | 3 (Bonus) | T009-01 → T009-08 (8 tasks)  | 003, 005     | ⬜ Not Started |


## Parallel Execution Map

```
Phase 0:  [000 Foundation] ──────────────────────────────────────────────
Phase 1:           ├── [001 Data] → [002 Embed] → [003 Retrieve] ───────
Phase 2:                                              ├── [004 Query] ──
                                                      │    └── [005 Gen]
                                                      │          └── [006 Cache]
Phase 3:                                              ├── [007 API] ────
                                                      │    └── [008 DB]
                                                      └── [009 Eval] ──
```

## Phase Exit Criteria Summary


| Phase       | Exit Criteria                                                                                                            |
| ----------- | ------------------------------------------------------------------------------------------------------------------------ |
| **Phase 0** | `make install && make test && make lint` passes. All modules importable.                                                 |
| **Phase 1** | Data pipeline produces valid `.jsonl`. FAISS index built and searchable. Baseline precision@5 measured.                  |
| **Phase 2** | End-to-end Q→A pipeline works. Query expansion improves recall. Caching operational. Metrics collected. Fallback tested. |
| **Phase 3** | All API endpoints functional. Database persists queries. Evaluation suite generates reports with all metrics.            |


---

## Review & Acceptance Checklist

- Each spec contains ONLY what/why — no technology names
- Each plan contains ALL technical decisions — technology names, architecture, data models
- Each task has a clear file path and definition of done
- No speculative "might need" features — every task traces to a user story
- All phases have clear prerequisites and exit criteria
- Constitution compliance is documented for every feature
- Dependency graph is acyclic and respects phase ordering
- Test tasks exist for every module
- Total scope is achievable within project timeline

---

*This master plan follows the Spec-Driven Development (SDD) methodology per GitHub's spec-kit. Each feature can be implemented using `/speckit.specify` → `/speckit.plan` → `/speckit.tasks` → `/speckit.implement` in sequence, using the specifications defined above as input.*