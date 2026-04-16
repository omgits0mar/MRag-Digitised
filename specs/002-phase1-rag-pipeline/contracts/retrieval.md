# Contract: Retrieval Service

**Module**: `src/mrag/retrieval/`

## Retriever Interface

### `RetrieverService(encoder: EmbeddingEncoder, indexer: FAISSIndexer, metadata_store: MetadataStore)`

High-level retrieval service composing embedding, search, and re-ranking.

### `RetrieverService.retrieve(request: RetrievalRequest) -> list[RetrievalResult]`

Execute a full retrieval: embed query → search index → fetch metadata → re-rank → filter → return.

**Input**: `RetrievalRequest` with query text and optional parameters

**Output**: List of `RetrievalResult` objects, sorted by `relevance_score` descending

**Behavior**:
1. Embed the query text using `EmbeddingEncoder.encode_single()`
2. Search FAISS index for `top_k` candidates (may over-fetch for threshold filtering)
3. Fetch metadata for each candidate from `MetadataStore`
4. Apply metadata filters if specified (remove non-matching)
5. Apply re-ranking via `rerank()` function
6. Apply score threshold filter if specified
7. Return up to `top_k` results

**Errors**: `RetrievalError` if index not loaded or encoding fails

**Guarantees**:
- Results are always sorted by `relevance_score` descending
- Result count <= `top_k`
- If `score_threshold` is set, all results have `relevance_score >= threshold`
- If `metadata_filters` are set, all results match all filters
- All `RetrievalResult` fields are populated (no null required fields)

---

## Ranking Interface

### `rerank(results: list[RawSearchResult], query: str, alpha: float = 0.7) -> list[RetrievalResult]`

Re-rank search results using weighted scoring.

**Input**:
- `results`: Raw search results with cosine similarity scores and metadata
- `query`: Original query text (for potential query-aware re-ranking)
- `alpha`: Weight for cosine similarity vs metadata boost (default 0.7)

**Output**: List of `RetrievalResult` with computed `relevance_score`, sorted descending

**Scoring formula**:
```
relevance_score = alpha * cosine_similarity + (1 - alpha) * metadata_boost
```

Where `metadata_boost` considers:
- Question type match between query pattern and result
- Answer availability (has_short_answer bonus)
- Domain relevance signal

**Guarantees**:
- `relevance_score` is in range [0.0, 1.0]
- Output is sorted by `relevance_score` descending
- Deterministic: same inputs always produce same output
