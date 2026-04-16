# Tasks: Phase 1 — RAG Foundation Pipeline

**Input**: Design documents from `/specs/002-phase1-rag-pipeline/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: Included — constitution Article VI mandates unit + integration tests per module.

**Organization**: Tasks grouped by user story for independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Extend existing project foundation with sample data fixtures and directory structure for Phase 1

- [x] T001 Create sample test data fixtures (100-row CSV, edge-case records) in tests/conftest.py
- [x] T002 [P] Ensure data directory structure exists: data/raw/, data/processed/, data/evaluation/

**Checkpoint**: Test fixtures available, data directories ready

---

## Phase 2: Foundational (Data Models — Blocking Prerequisites)

**Purpose**: Shared Pydantic data models used across multiple user stories. MUST complete before any user story.

- [x] T003 Create data models (RawRecord, ProcessedDocument, TextChunk, DocumentMetadata, PipelineResult) in src/mrag/data/models.py
- [x] T004 Create unit tests for data models (validation, constraints, edge cases) in tests/unit/test_data_models.py

**Checkpoint**: All data models importable, validation works. `python -c "from mrag.data.models import ProcessedDocument, TextChunk"` succeeds.

---

## Phase 3: User Story 1 — Dataset Ingestion & Processing (Priority: P1) MVP

**Goal**: Load the Natural Questions dataset, validate schema, clean records, handle malformed input gracefully.

**Independent Test**: Run ingestion on 100-row sample — all valid records parsed, malformed records logged and skipped, no data loss.

### Tests for User Story 1

- [x] T005 [P] [US1] Create unit tests for ingestion (valid CSV, malformed records, missing columns, empty rows, encoding) in tests/unit/test_ingestion.py

### Implementation for User Story 1

- [x] T006 [US1] Implement load_dataset() with Pandas CSV/JSON loading, RawRecord validation, skip-and-log for malformed records in src/mrag/data/ingestion.py

**Checkpoint**: `load_dataset("tests/fixtures/sample.csv")` returns list of RawRecord, logs skipped records. Tests pass.

---

## Phase 4: User Story 2 — Text Chunking (Priority: P1)

**Goal**: Split long-form text into retrieval-optimized, sentence-boundary-aligned chunks with configurable size and overlap.

**Independent Test**: Chunk a 2000-word document — chunks respect size/overlap, sentence boundaries preserved, deterministic output.

### Tests for User Story 2

- [x] T007 [P] [US2] Create unit tests for chunking (sizes, overlap, sentence boundaries, short text, unicode, determinism) in tests/unit/test_chunking.py

### Implementation for User Story 2

- [x] T008 [US2] Implement TextChunker class with sliding window, sentence-boundary alignment, configurable chunk_size and chunk_overlap in src/mrag/data/chunking.py

**Checkpoint**: `TextChunker(512, 50).chunk(text, "doc1")` returns list of TextChunk with correct boundaries. Tests pass.

---

## Phase 5: User Story 3 — Metadata Enrichment (Priority: P2)

**Goal**: Classify question type, domain, difficulty for each question-answer pair. All metadata fields populated, no nulls.

**Independent Test**: Enrich 50 samples — "Who is..." → factoid, "Explain..." → descriptive, difficulty matches answer availability.

### Tests for User Story 3

- [x] T009 [P] [US3] Create unit tests for enrichment (question type patterns, domain classification, difficulty scoring, edge cases) in tests/unit/test_enrichment.py

### Implementation for User Story 3

- [x] T010 [US3] Implement question type classifier (regex-based: factoid, descriptive, list, yes_no, unknown) in src/mrag/data/enrichment.py
- [x] T011 [US3] Implement domain classifier (TF-IDF with predefined domain keywords) in src/mrag/data/enrichment.py
- [x] T012 [US3] Implement difficulty scorer and enrich() function combining all classifiers in src/mrag/data/enrichment.py

**Checkpoint**: `enrich("Who is Einstein?", "physicist", "Albert Einstein was...")` returns DocumentMetadata with question_type="factoid". Tests pass.

---

## Phase 6: User Story 7 — Data Export & Pipeline Orchestration (Priority: P2)

**Goal**: Export processed documents to JSONL with deterministic 90/10 train/eval split. Orchestrate full data pipeline.

**Independent Test**: Process 1000 records end-to-end, verify JSONL output, 90/10 split is deterministic across runs.

### Tests for User Story 7

- [x] T013 [P] [US7] Create unit tests for export (JSONL format, split ratio, determinism, field preservation) in tests/unit/test_export.py
- [x] T014 [P] [US7] Create integration test for full data pipeline (100-row end-to-end) in tests/integration/test_data_pipeline.py

### Implementation for User Story 7

- [x] T015 [US7] Implement export_jsonl() with JSONL serialization, train_test_split with fixed seed, statistics logging in src/mrag/data/export.py
- [x] T016 [US7] Implement run_pipeline() orchestrating ingest → chunk → enrich → export with validation at each boundary in src/mrag/data/pipeline.py

**Checkpoint**: `run_pipeline(config)` produces train.jsonl + eval.jsonl in data/processed/. Integration test passes end-to-end.

---

## Phase 7: User Story 4 — Multilingual Embedding Generation (Priority: P1)

**Goal**: Generate L2-normalized multilingual embeddings for all text chunks using sentence-transformers with batch processing.

**Independent Test**: Embed "What is water?" in English and Arabic — cosine similarity > 0.7. All vectors have consistent dimensionality and are unit-normalized.

### Tests for User Story 4

- [x] T017 [P] [US4] Create unit tests for encoder (single/batch encoding, L2 normalization, cross-lingual similarity, empty input, dimension consistency) in tests/unit/test_encoder.py

### Implementation for User Story 4

- [x] T018 [US4] Implement EmbeddingEncoder class wrapping SentenceTransformer with lazy loading, encode() batch method with L2 normalization, encode_single() convenience method in src/mrag/embeddings/encoder.py

**Checkpoint**: `EmbeddingEncoder().encode(["hello", "world"])` returns (2, 384) L2-normalized ndarray. Cross-lingual test passes. Tests pass.

---

## Phase 8: User Story 5 — Vector Index Construction & Persistence (Priority: P1)

**Goal**: Build FAISS IndexFlatIP from embeddings, persist to disk, load without recomputing. Store parallel metadata with O(1) lookup.

**Independent Test**: Index 1000 vectors, save/load roundtrip, search returns correct top-5 with metadata.

### Tests for User Story 5

- [x] T019 [P] [US5] Create unit tests for FAISSIndexer (build, search accuracy, save/load roundtrip, dimension validation) in tests/unit/test_indexer.py
- [x] T020 [P] [US5] Create unit tests for MetadataStore (add, get, filter, save/load, key errors) in tests/unit/test_metadata_store.py
- [x] T021 [P] [US5] Create integration test for embedding pipeline (100-chunk embed → index → search) in tests/integration/test_embedding_pipeline.py

### Implementation for User Story 5

- [x] T022 [US5] Implement FAISSIndexer class with IndexFlatIP, build_index(), search(), save(), load(), dimension validation in src/mrag/embeddings/indexer.py
- [x] T023 [US5] Implement MetadataStore class with JSON-backed dict, add(), get(), filter(), save(), load() in src/mrag/embeddings/metadata_store.py
- [x] T024 [US5] Implement run_embedding_pipeline() orchestrating load JSONL → embed → index → save metadata in src/mrag/embeddings/pipeline.py

**Checkpoint**: `run_embedding_pipeline(config, "data/processed/train.jsonl")` produces index.faiss + metadata.json. Integration test passes.

---

## Phase 9: User Story 6 — Basic Retrieval Pipeline (Priority: P1)

**Goal**: Accept natural language query, embed it, search the index, re-rank with metadata signals, return structured results with configurable top-K, score threshold, and metadata filters.

**Independent Test**: Query "What is photosynthesis?" returns biology-related chunk in top-3, all results have complete metadata, ordered by relevance score.

### Tests for User Story 6

- [x] T025 [P] [US6] Create unit tests for ranking (weighted scoring formula, determinism, score bounds, sort order) in tests/unit/test_ranking.py
- [x] T026 [P] [US6] Create unit tests for retriever (top-K enforcement, threshold filtering, metadata filtering, empty results) in tests/unit/test_retriever.py
- [x] T027 [P] [US6] Create integration test for retrieval pipeline (natural language query → ranked results with metadata) in tests/integration/test_retrieval_pipeline.py

### Implementation for User Story 6

- [x] T028 [US6] Create RetrievalRequest and RetrievalResult Pydantic models in src/mrag/retrieval/models.py
- [x] T029 [US6] Implement rerank() with weighted scoring (alpha * cosine_sim + (1-alpha) * metadata_boost), metadata boost computation, score capping in src/mrag/retrieval/ranking.py
- [x] T030 [US6] Implement RetrieverService class composing encoder + indexer + metadata_store + ranking with over-fetch, metadata filtering, threshold filtering in src/mrag/retrieval/retriever.py

**Checkpoint**: `RetrieverService.retrieve(RetrievalRequest(query="What is photosynthesis?"))` returns ranked results with complete metadata. All tests pass. End of Phase 1 pipeline functional.

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, lint compliance, and end-to-end verification

- [x] T031 Run `make lint` and fix any ruff/black violations across all new files in src/mrag/data/, src/mrag/embeddings/, src/mrag/retrieval/
- [x] T032 Run `make test` and ensure all unit + integration tests pass with zero failures
- [x] T033 Validate quickstart.md scenarios work end-to-end on sample data

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories
- **US1 Ingestion (Phase 3)**: Depends on Phase 2 (data models)
- **US2 Chunking (Phase 4)**: Depends on Phase 2 (data models) — can run in PARALLEL with US1
- **US3 Enrichment (Phase 5)**: Depends on Phase 2 (data models) — can run in PARALLEL with US1, US2
- **US7 Export & Pipeline (Phase 6)**: Depends on US1 + US2 + US3 (orchestrates all data stages)
- **US4 Embedding (Phase 7)**: Depends on Phase 2 (data models) — can start after Phase 2, but integration needs US7 output
- **US5 Indexing (Phase 8)**: Depends on US4 (needs encoder)
- **US6 Retrieval (Phase 9)**: Depends on US4 + US5 (needs encoder + indexer + metadata store)
- **Polish (Phase 10)**: Depends on all user stories complete

### User Story Dependencies

```
Phase 2 (Foundational)
    ├── US1 (Ingestion) ──────┐
    ├── US2 (Chunking) ───────┤── US7 (Export & Pipeline)
    ├── US3 (Enrichment) ─────┘
    │
    └── US4 (Embedding) ──── US5 (Indexing) ──── US6 (Retrieval)
```

- **US1, US2, US3**: Can run in PARALLEL after Phase 2
- **US4**: Can run in PARALLEL with US1/US2/US3 (unit tests only need data models, not pipeline output)
- **US7**: Requires US1 + US2 + US3 complete
- **US5**: Requires US4 complete
- **US6**: Requires US4 + US5 complete

### Within Each User Story

1. Tests written first (TDD: ensure they fail)
2. Implementation to make tests pass
3. Checkpoint validation before moving to next story

### Parallel Opportunities

```bash
# After Phase 2 completes, launch US1 + US2 + US3 + US4 in parallel:
Task: T005 (US1 tests) | T007 (US2 tests) | T009 (US3 tests) | T017 (US4 tests)
Task: T006 (US1 impl)  | T008 (US2 impl)  | T010-12 (US3 impl) | T018 (US4 impl)

# After US1+US2+US3 complete, launch US7:
Task: T013-T014 (US7 tests) → T015-T016 (US7 impl)

# After US4 completes, launch US5:
Task: T019-T021 (US5 tests) → T022-T024 (US5 impl)

# After US5 completes, launch US6:
Task: T025-T027 (US6 tests) → T028-T030 (US6 impl)
```

---

## Implementation Strategy

### MVP First (US1 + US2 → basic data pipeline)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (data models)
3. Complete Phase 3: US1 (Ingestion) — can load and validate data
4. Complete Phase 4: US2 (Chunking) — can chunk text
5. **STOP and VALIDATE**: Ingest + chunk a sample dataset independently

### Full Data Pipeline (add US3 + US7)

6. Complete Phase 5: US3 (Enrichment) — metadata classification
7. Complete Phase 6: US7 (Export & Pipeline) — full data pipeline end-to-end
8. **STOP and VALIDATE**: `run_pipeline()` produces train.jsonl + eval.jsonl

### Full Phase 1 (add US4 + US5 + US6)

9. Complete Phase 7: US4 (Embedding) — multilingual embeddings
10. Complete Phase 8: US5 (Indexing) — FAISS vector index + metadata store
11. Complete Phase 9: US6 (Retrieval) — query → ranked results
12. **STOP and VALIDATE**: Full pipeline from raw data to retrieval query
13. Complete Phase 10: Polish — lint, test, quickstart validation

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- Constitution Article VI: tests are mandatory per module
- Constitution Article IX: all code must pass black + ruff with zero violations
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
