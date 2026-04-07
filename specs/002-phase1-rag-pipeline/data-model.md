# Data Model: Phase 1 — RAG Foundation Pipeline

**Branch**: `002-phase1-rag-pipeline` | **Date**: 2026-04-07

## Entity Definitions

### RawRecord

The raw input from the Natural Questions dataset before any processing.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| question_text | str | required, non-empty | The natural language question |
| short_answer | str \| None | optional | Concise answer if available |
| long_answer | str | required, non-empty | Long-form answer / document context |
| document_title | str \| None | optional | Source document title |
| document_url | str \| None | optional | Source document URL |

**Validation rules**:
- `question_text` must be non-empty after whitespace stripping
- `long_answer` must be non-empty after whitespace stripping
- Records failing validation are logged and skipped

---

### ProcessedDocument

A fully processed document ready for embedding. One per question-answer pair.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| doc_id | str | unique, auto-generated (UUID) | Unique document identifier |
| question | str | required, non-empty | Cleaned question text |
| answer_short | str \| None | optional | Short-form answer if available |
| answer_long | str | required, non-empty | Long-form answer text |
| answer_type | str | enum: "short", "long", "both" | Which answer forms are present |
| chunks | list[TextChunk] | min length 1 | Chunked text segments |
| metadata | DocumentMetadata | required | Enrichment data |

**Relationships**:
- Contains 1..N `TextChunk` entities
- Contains exactly 1 `DocumentMetadata` entity

---

### TextChunk

A segment of text derived from a document, sized for embedding and retrieval.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| chunk_id | str | unique, format: `{doc_id}_chunk_{index}` | Unique chunk identifier |
| doc_id | str | foreign key → ProcessedDocument | Parent document reference |
| text | str | required, non-empty | The chunk text content |
| start_pos | int | >= 0 | Character start position in source |
| end_pos | int | > start_pos | Character end position in source |
| token_count | int | > 0 | Number of tokens in this chunk |
| chunk_index | int | >= 0 | Position within parent document |
| total_chunks | int | >= 1 | Total chunks in parent document |

**Validation rules**:
- `end_pos` > `start_pos`
- `chunk_index` < `total_chunks`
- `text` must be non-empty after stripping

---

### DocumentMetadata

Enrichment data attached to a processed document and its chunks.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| question_type | str | enum: "factoid", "descriptive", "list", "yes_no", "unknown" | Classified question type |
| domain | str | non-empty | Auto-classified domain (e.g., "science", "history") |
| difficulty | str | enum: "easy", "medium", "hard" | Difficulty level based on answer availability |
| has_short_answer | bool | required | Whether a short answer exists |
| source_id | str | required | Reference to source dataset record |
| language | str | default: "en" | Detected language code |

**Classification rules**:
- `difficulty`: "easy" if short answer available, "medium" if long-only, "hard" if ambiguous/partial
- `question_type`: Rule-based classification from question text patterns

---

### EmbeddingRecord

The vector representation of a text chunk, ready for indexing.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| chunk_id | str | foreign key → TextChunk | Source chunk reference |
| vector | ndarray (float32) | shape: (384,), L2-normalized | Dense embedding vector |
| faiss_index_id | int | auto-assigned, sequential | FAISS internal integer ID |

**Validation rules**:
- Vector must have exactly 384 dimensions (matching model output)
- Vector must be L2-normalized (unit length, tolerance 1e-6)

---

### MetadataEntry

The parallel metadata stored alongside the FAISS index for result enrichment.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| faiss_index_id | int | primary key | FAISS internal integer ID |
| chunk_id | str | required | Reference to source chunk |
| doc_id | str | required | Reference to parent document |
| chunk_text | str | required | Full text of the chunk |
| question | str | required | Original question |
| answer_short | str \| None | optional | Short-form answer |
| answer_long | str | required | Long-form answer |
| question_type | str | required | From DocumentMetadata |
| domain | str | required | From DocumentMetadata |
| difficulty | str | required | From DocumentMetadata |
| has_short_answer | bool | required | From DocumentMetadata |

---

### RetrievalRequest

Input to the retrieval pipeline.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| query | str | required, non-empty | Natural language question |
| top_k | int | >= 1, default: 5 | Number of results to return |
| score_threshold | float \| None | 0.0–1.0 if set | Minimum relevance score filter |
| metadata_filters | dict[str, str] \| None | optional | Key-value filters (e.g., domain="science") |

---

### RetrievalResult

Output from the retrieval pipeline for a single matched chunk.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| chunk_id | str | required | Matched chunk identifier |
| doc_id | str | required | Parent document identifier |
| chunk_text | str | required | Full text of matched chunk |
| relevance_score | float | 0.0–1.0 | Combined relevance score after re-ranking |
| cosine_similarity | float | -1.0–1.0 | Raw cosine similarity from FAISS |
| question | str | required | Original question from source |
| answer_short | str \| None | optional | Short-form answer if available |
| answer_long | str | required | Long-form answer |
| question_type | str | required | Question classification |
| domain | str | required | Domain classification |
| difficulty | str | required | Difficulty level |
| has_short_answer | bool | required | Short answer availability flag |

## Entity Relationship Diagram

```
RawRecord (input)
    │
    ▼ [ingestion + validation]
ProcessedDocument
    ├── 1..N TextChunk
    └── 1    DocumentMetadata
              │
              ▼ [embedding]
         EmbeddingRecord (per TextChunk)
              │
              ▼ [indexing]
         FAISS Index + MetadataEntry (per EmbeddingRecord)
              │
              ▼ [retrieval]
         RetrievalRequest → RetrievalResult[]
```

## State Transitions

### Pipeline Processing States

```
RAW → VALIDATED → CHUNKED → ENRICHED → EMBEDDED → INDEXED → SEARCHABLE
```

| State | Description | Stored As |
|-------|-------------|-----------|
| RAW | Source dataset record | CSV/JSON file |
| VALIDATED | Schema-validated, cleaned record | In-memory ProcessedDocument (partial) |
| CHUNKED | Text split into chunks | In-memory ProcessedDocument (with chunks) |
| ENRICHED | Metadata classifications added | In-memory ProcessedDocument (complete) |
| EMBEDDED | Vector representations generated | In-memory ndarray |
| INDEXED | Added to FAISS index + metadata store | `.faiss` file + `.json` metadata file |
| SEARCHABLE | Ready for retrieval queries | Loaded index in memory |
