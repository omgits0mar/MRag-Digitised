# Feature Specification: Phase 2 RAG Pipeline — Query Processing, Response Generation & Caching

**Feature Branch**: `003-phase2-rag-pipeline`  
**Created**: 2026-04-08  
**Status**: Draft  
**Input**: User description: "Build phase 2 for the project: features 004 (Query Processing), 005 (Response Generation), 006 (Caching & Performance). Use conda environment 'mrag'. Utilize Apple Silicon (no NVIDIA GPU)."

## Clarifications

### Session 2026-04-08

- Q: Multi-turn coreference resolution approach (heuristic vs LLM-assisted)? → A: Heuristic — prepend recent conversation history to the query string without an extra LLM call. Keeps query processing under 10ms latency target.
- Q: Cache matching strategy for near-identical queries? → A: Exact match on normalized query hash. Query normalization (FR-001) handles most near-identical variants; no embedding similarity lookup needed.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Intelligent Query Preprocessing & Enhancement (Priority: P1)

As a user asking questions, I want my queries to be cleaned, normalized, and expanded so that retrieval quality is maximized regardless of how I phrase my question.

**Why this priority**: Query quality directly determines retrieval quality. Without proper preprocessing and expansion, even perfect retrieval and generation components will return poor results for ambiguous, misspelled, or terse queries.

**Independent Test**: Submit a query with extra whitespace, mixed casing, and unicode characters. Verify the preprocessor normalizes it and the expander adds relevant terms that improve retrieval precision@5 compared to the raw query.

**Acceptance Scenarios**:

1. **Given** a query "  What  IS   Photosynthesis?? ", **When** preprocessing runs, **Then** the output is "what is photosynthesis" with consistent casing, collapsed whitespace, and normalized unicode
2. **Given** a short query "DNA", **When** query expansion runs, **Then** additional related terms are appended (e.g., "deoxyribonucleic acid", "genetics") and recall@10 improves by at least 10% vs. the unexpanded query
3. **Given** a conversation history of ["What is DNA?", "How is it structured?"] and a follow-up "What about its function?", **When** contextualization runs, **Then** the system resolves "its" to "DNA" and retrieves results about DNA function
4. **Given** a query in Arabic or French, **When** preprocessing runs, **Then** unicode normalization is applied correctly and the query passes through without corruption

---

### User Story 2 - LLM-Powered Response Generation (Priority: P1)

As a user, I want natural language answers generated from retrieved passages so that I get coherent, grounded responses instead of raw document chunks.

**Why this priority**: Response generation is the core user-facing value of the RAG system. Without it, users only see ranked chunks with no synthesis or explanation.

**Independent Test**: Ask a factual question about the dataset, verify the answer is derived from retrieved context passages and includes citations. Then ask an out-of-domain question and verify the system returns a low-confidence fallback response.

**Acceptance Scenarios**:

1. **Given** a factual question and relevant retrieved passages, **When** the generation pipeline runs, **Then** a coherent answer is produced that directly references information from the passages
2. **Given** a question where no retrieved passage scores above the confidence threshold, **When** generation runs, **Then** the system returns a fallback response indicating insufficient information with a low confidence score
3. **Given** an updated prompt template file on disk, **When** the next query is processed, **Then** the new template is used without requiring a service restart
4. **Given** a generated response that lacks grounding in retrieved context, **When** validation runs, **Then** the confidence score is below the threshold and the fallback mechanism triggers

---

### User Story 3 - Response Caching for Repeated Queries (Priority: P2)

As a system operator, I want query results cached so that repeated questions (after normalization) are served instantly without re-computing embeddings, search, or LLM generation.

**Why this priority**: Caching is critical for production performance and cost control (LLM API calls are expensive), but the system is functional without it. It enhances rather than enables the core capability.

**Independent Test**: Send the same query twice. Verify the second response arrives in under 50ms with a cache hit indicator, and the response content is identical to the first.

**Acceptance Scenarios**:

1. **Given** a query that was previously answered, **When** the same query arrives again, **Then** the cached result is returned without re-embedding, re-searching, or re-generating
2. **Given** a cached response older than the configured TTL, **When** the query arrives again, **Then** the cache miss triggers fresh computation and the cache is updated
3. **Given** the embedding cache is at max capacity, **When** a new query arrives, **Then** the least-recently-used embedding is evicted to make room

---

### User Story 4 - Batch Query Processing (Priority: P2)

As a data engineer, I want batch processing so that I can run evaluation workloads or re-index queries efficiently with optimized throughput.

**Why this priority**: Essential for evaluation and benchmarking workflows, but not required for single-query interactive use.

**Independent Test**: Submit a batch of 100 queries. Verify throughput is at least 3x the single-query sequential throughput and all results are correct.

**Acceptance Scenarios**:

1. **Given** a list of 100 queries, **When** batch processing runs, **Then** all queries are processed with batched embedding and search operations
2. **Given** batch processing is in progress, **When** one query in the batch fails, **Then** processing continues for remaining queries and the failure is logged

---

### User Story 5 - Performance Metrics Collection (Priority: P3)

As a system operator, I want performance metrics collected on every request so that I can monitor system health and identify bottlenecks across embedding, search, LLM generation, and cache stages.

**Why this priority**: Metrics are observability infrastructure. The system works without them, but diagnosing performance issues is impractical without per-stage timing data.

**Independent Test**: Process 10 queries. Verify each has metrics recorded for embedding_time_ms, search_time_ms, llm_time_ms, total_time_ms, and cache_hit.

**Acceptance Scenarios**:

1. **Given** any query processed by the system, **When** the request completes, **Then** per-stage timing metrics are recorded
2. **Given** accumulated metrics, **When** a summary is requested, **Then** p50, p95, p99 latency statistics are computed for each stage

---

### Edge Cases

- What happens when the LLM API is unreachable or times out? System returns fallback response with logged error.
- What happens when conversation history exceeds the context window? History is truncated using a sliding window of the most recent turns.
- What happens when a query expands to terms that worsen retrieval? Expansion is weighted; original query terms always dominate.
- What happens when the cache is corrupted or stale? Cache misses gracefully fall through to fresh computation.
- What happens when batch processing receives an empty list? Returns empty results immediately without error.
- How does the system behave on Apple Silicon without NVIDIA GPU? All computation (embedding, FAISS) runs on CPU via Apple's Accelerate framework; no CUDA dependency required.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST normalize user queries by collapsing whitespace, lowercasing, normalizing unicode (NFC), and stripping excessive punctuation before embedding
- **FR-002**: System MUST support query expansion via pseudo-relevance feedback — embed query, retrieve top-N, extract key terms, append to query for a second retrieval pass
- **FR-003**: System MUST maintain multi-turn conversation context using a sliding window of recent turns, prepending prior query-response history to the current query for implicit reference resolution (heuristic approach, no additional LLM call)
- **FR-004**: System MUST integrate with an LLM API (Groq-compatible interface) to generate natural language answers grounded in retrieved context passages
- **FR-005**: System MUST use an abstract LLM client interface (BaseLLMClient) so that the LLM provider can be swapped without modifying downstream code
- **FR-006**: System MUST load prompt templates from the filesystem (Jinja2 format) and support hot-reloading without service restart
- **FR-007**: System MUST compute a confidence score for each generated response based on retrieval score aggregation and answer-context overlap
- **FR-008**: System MUST return a fallback response with a low confidence score when no sufficiently relevant context is found (all retrieval scores below threshold)
- **FR-009**: System MUST cache query embeddings using an LRU cache with configurable maximum size
- **FR-010**: System MUST cache full responses using a TTL-based cache keyed by normalized query hash (exact match after normalization), with automatic expiration
- **FR-011**: System MUST support batch processing of multiple queries with batched embedding and search for optimized throughput
- **FR-012**: System MUST collect per-request performance metrics: embedding_time_ms, search_time_ms, llm_time_ms, total_time_ms, cache_hit
- **FR-013**: System MUST provide aggregate metric statistics (p50, p95, p99 latency) across accumulated requests
- **FR-014**: System MUST run entirely on CPU/Apple Silicon without any NVIDIA GPU or CUDA dependency
- **FR-015**: System MUST handle LLM API errors gracefully with configurable retry logic and fallback to cached or canned responses

### Key Entities

- **ProcessedQuery**: A user query after normalization, expansion, and contextualization — carries the original text, expanded terms, and conversation history
- **GeneratedResponse**: The LLM-generated answer including the response text, confidence score, source citations, and per-stage timing metrics
- **CacheEntry**: A cached response keyed by query hash with TTL metadata
- **RequestMetrics**: Per-request timing breakdown for each pipeline stage (embedding, search, generation, total) and cache hit indicator

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users receive coherent, context-grounded answers for 90%+ of in-domain questions
- **SC-002**: Query preprocessing adds less than 10 milliseconds of latency to the pipeline
- **SC-003**: Query expansion improves recall@10 by at least 10% on ambiguous or short queries compared to raw queries
- **SC-004**: Multi-turn context correctly resolves pronoun references in 80%+ of test conversation scenarios
- **SC-005**: Fallback response is returned for 95%+ of out-of-domain questions where no relevant context exists
- **SC-006**: Repeated identical queries are served from cache in under 50 milliseconds
- **SC-007**: Batch processing throughput is at least 3x the sequential single-query throughput
- **SC-008**: End-to-end latency (query processing + retrieval + generation) is under 3 seconds at the 95th percentile
- **SC-009**: Performance metrics collection adds less than 5 milliseconds overhead per request
- **SC-010**: All components run correctly on Apple Silicon hardware without GPU acceleration dependencies

## Assumptions

- Phase 1 (data processing, embedding, vector store, basic retrieval) is complete and the FAISS index is built and searchable
- The Groq API (or compatible LLM API) is accessible via an API key stored in environment variables
- The conda environment 'mrag' has all required packages installed and is the target execution environment
- The development machine uses Apple Silicon (M-series chip) — all computation uses CPU with Apple's Accelerate framework via NumPy/FAISS; no CUDA or NVIDIA dependencies
- Conversation history is managed in-memory per session; persistence is deferred to Phase 3 (database integration)
- The existing retrieval module (`src/mrag/retrieval/`) built in Phase 1 is the foundation for the query and generation pipelines
- Prompt template files are stored under `prompts/templates/` in Jinja2 format
- Cache sizes and TTL values are configurable via the existing Pydantic Settings configuration system
