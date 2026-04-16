# Data Model: Phase 2 RAG Pipeline

**Branch**: `003-phase2-rag-pipeline` | **Date**: 2026-04-08

## Entity Diagram

```
ConversationTurn ──1:N──→ ProcessedQuery
ProcessedQuery ──1:1──→ ExpandedQuery
ProcessedQuery ──1:N──→ RetrievalResult (from Phase 1)
RetrievalResult ──N:1──→ GeneratedResponse
GeneratedResponse ──1:1──→ ValidationResult
GeneratedResponse ──1:1──→ RequestMetrics
ProcessedQuery ──0:1──→ CacheEntry (ResponseCache)
```

## Entities

### ProcessedQuery

A user query after all preprocessing stages.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| original_query | str | min_length=1 | Raw user input before any processing |
| normalized_query | str | min_length=1 | After NFC normalization, lowercasing, whitespace collapse |
| expanded_query | str | nullable | After pseudo-relevance feedback expansion |
| final_query | str | min_length=1 | The query sent to the embedding encoder |
| conversation_history | list[ConversationTurn] | max_length=5 | Recent conversation turns (sliding window) |
| query_hash | str | 32-char hex | MD5 hash of normalized_query for cache keying |
| expansion_terms | list[str] | max_length=5 | Terms added by query expansion |

### ConversationTurn

A single turn in a multi-turn conversation.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| query | str | min_length=1 | The user's question in this turn |
| response | str | nullable | The system's response (None if not yet answered) |
| timestamp | float | positive | Unix timestamp of the turn |

### ExpandedQuery

Result of pseudo-relevance feedback expansion.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| original_query | str | min_length=1 | Pre-expansion query text |
| expanded_query | str | min_length=1 | Post-expansion query text |
| expansion_terms | list[str] | | Terms extracted from PRF documents |
| prf_doc_ids | list[str] | | IDs of documents used for feedback |

### GeneratedResponse

The final output of the generation pipeline.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| query | str | | Original user query |
| answer | str | | Generated answer text |
| confidence_score | float | 0.0–1.0 | Confidence based on retrieval + overlap |
| is_fallback | bool | | True if fallback response was used |
| sources | list[SourceCitation] | | Retrieved passages cited in the answer |
| metrics | RequestMetrics | | Timing breakdown for this request |

### SourceCitation

A reference to a retrieved passage used in generation.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| chunk_id | str | | ID of the cited chunk |
| doc_id | str | | Parent document ID |
| chunk_text | str | | Text of the passage |
| relevance_score | float | 0.0–1.0 | Retrieval relevance score |

### ValidationResult

Output of response quality validation.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| confidence_score | float | 0.0–1.0 | Computed confidence |
| retrieval_score_avg | float | 0.0–1.0 | Mean retrieval score of top-K |
| context_overlap | float | 0.0–1.0 | TF-IDF overlap between answer and context |
| is_confident | bool | | True if score >= threshold |
| threshold_used | float | 0.0–1.0 | Confidence threshold at time of validation |

### RequestMetrics

Per-request timing data.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| preprocessing_time_ms | float | >= 0 | Query normalization + expansion time |
| embedding_time_ms | float | >= 0 | Query embedding time |
| search_time_ms | float | >= 0 | FAISS search + re-ranking time |
| llm_time_ms | float | >= 0 | LLM API call time |
| total_time_ms | float | >= 0 | End-to-end request time |
| cache_hit | bool | | Whether response was served from cache |
| cache_type | str | nullable, one of: "embedding", "response", None | Which cache layer hit |

### CacheEntry

Internal structure for the response cache.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| query_hash | str | 32-char hex | MD5 of normalized query |
| response | GeneratedResponse | | Cached response object |
| created_at | float | positive | Unix timestamp of cache insertion |
| expires_at | float | positive | Unix timestamp of TTL expiration |

## State Transitions

### Query Processing Flow

```
RAW → NORMALIZED → CONTEXTUALIZED → EXPANDED → EMBEDDED → RETRIEVED → GENERATED → VALIDATED
```

### Cache States

```
MISS → COMPUTE → STORE
HIT → RETURN (skip COMPUTE)
EXPIRED → evict → MISS
EVICTED (LRU) → MISS
```

## Relationships to Phase 1 Entities

- `ProcessedQuery.final_query` is passed to `EmbeddingEncoder.encode_single()` → produces query vector
- `RetrieverService.retrieve()` returns `list[RetrievalResult]` (Phase 1 model) → consumed by `GenerationPipeline`
- `MetadataEntry` (Phase 1) provides context fields (question, answer_short, answer_long) → injected into prompt template
