# Tasks: Phase 2 RAG Pipeline — Query Processing, Response Generation & Caching

**Input**: Design documents from `/specs/003-phase2-rag-pipeline/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: Included per Constitution Article VI (testing is mandatory for every module).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add Phase 2 dependencies, config fields, and prompt templates

- [x] T001 Add Jinja2 dependency to pyproject.toml and install with `pip install -e ".[dev]"`
- [x] T002 Add Phase 2 config fields to src/mrag/config.py: query_expansion_enabled (bool, True), query_expansion_top_n (int, 3), conversation_history_max_turns (int, 5), confidence_threshold (float, 0.3), llm_timeout_seconds (int, 30), llm_max_retries (int, 3) with validators
- [x] T003 [P] Create Jinja2 Q&A prompt template in prompts/templates/qa_prompt.j2 — accepts query, context_chunks (list with chunk_text, relevance_score, question, answer_short, answer_long), and conversation_history; formats context as numbered passages with citations
- [x] T004 [P] Create Jinja2 system prompt template in prompts/templates/system_prompt.j2 — instructs LLM to answer based only on provided context, cite sources, and admit uncertainty when context is insufficient
- [x] T005 [P] Create Jinja2 fallback prompt template in prompts/templates/fallback_prompt.j2 — polite response indicating insufficient information to answer the question

**Checkpoint**: `pip install -e ".[dev]"` succeeds. Config loads with new fields. Template files exist.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Pydantic models shared across all user stories

**CRITICAL**: No user story work can begin until this phase is complete

- [x] T006 [P] Create query Pydantic models in src/mrag/query/models.py: ConversationTurn (query: str, response: str | None, timestamp: float), ExpandedQuery (original_query, expanded_query, expansion_terms: list[str], prf_doc_ids: list[str]), ProcessedQuery (original_query, normalized_query, expanded_query: str | None, final_query, conversation_history: list[ConversationTurn], query_hash: str, expansion_terms: list[str])
- [x] T007 [P] Create generation Pydantic models in src/mrag/generation/models.py: SourceCitation (chunk_id, doc_id, chunk_text, relevance_score: float), ValidationResult (confidence_score, retrieval_score_avg, context_overlap, is_confident: bool, threshold_used: float), GeneratedResponse (query, answer, confidence_score, is_fallback: bool, sources: list[SourceCitation], metrics: RequestMetrics)
- [x] T008 [P] Create cache/metrics Pydantic model in src/mrag/cache/models.py: RequestMetrics (preprocessing_time_ms, embedding_time_ms, search_time_ms, llm_time_ms, total_time_ms, cache_hit: bool, cache_type: str | None)

**Checkpoint**: All models importable. `from mrag.query.models import ProcessedQuery` works. `from mrag.generation.models import GeneratedResponse` works. `from mrag.cache.models import RequestMetrics` works.

---

## Phase 3: User Story 1 — Intelligent Query Preprocessing & Enhancement (Priority: P1)

**Goal**: Normalize, contextualize, and expand user queries to maximize retrieval quality

**Independent Test**: Submit "  What  IS   Photosynthesis?? " → get "what is photosynthesis". Submit short query "DNA" with expansion → get additional terms. Multi-turn conversation resolves pronouns via history prepend.

### Tests for User Story 1

- [x] T009 [P] [US1] Create unit tests in tests/unit/test_preprocessor.py — test normalize() with: extra whitespace, mixed casing, unicode (Arabic, French, Chinese), excessive punctuation, empty-after-normalization error, NFC normalization
- [x] T010 [P] [US1] Create unit tests in tests/unit/test_context_manager.py — test add_turn(), get_contextualized_query() with: empty history, single turn, max_turns sliding window truncation, clear()
- [x] T011 [P] [US1] Create unit tests in tests/unit/test_expander.py — test expand() with: short query produces expansion terms, expansion preserves original query terms, disabled expansion returns original, mock retriever for PRF
- [x] T012 [P] [US1] Create unit tests in tests/unit/test_query_pipeline.py — test process() end-to-end: normalization + context + expansion chained, expansion disabled path, no context_manager path

### Implementation for User Story 1

- [x] T013 [P] [US1] Implement QueryPreprocessor in src/mrag/query/preprocessor.py — normalize() method: unicodedata.normalize("NFC"), lowercase, re.sub for whitespace collapse, strip trailing repeated punctuation, raise QueryProcessingError if empty after normalization, structured logging
- [x] T014 [P] [US1] Implement ConversationContextManager in src/mrag/query/context_manager.py — __init__(max_turns: int = 5), add_turn(query, response), get_contextualized_query(current_query) prepends "Previous Q: ... A: ..." from sliding window, clear() resets history
- [x] T015 [US1] Implement QueryExpander in src/mrag/query/expander.py — __init__(retriever, encoder), expand(query, top_n=3, max_terms=5) performs pseudo-relevance feedback: retrieve top_n docs, extract TF-IDF terms from chunk_text, append to original query weighted by score; depends on T013 for normalized input
- [x] T016 [US1] Implement QueryPipeline in src/mrag/query/pipeline.py — __init__(preprocessor, expander, context_manager), process(query, expand=True) chains: normalize → contextualize → expand → compute MD5 query_hash → return ProcessedQuery; structured logging at each stage
- [x] T017 [US1] Update src/mrag/query/__init__.py with public exports: QueryPreprocessor, QueryExpander, ConversationContextManager, QueryPipeline, ProcessedQuery, ExpandedQuery, ConversationTurn

**Checkpoint**: `pytest tests/unit/test_preprocessor.py tests/unit/test_context_manager.py tests/unit/test_expander.py tests/unit/test_query_pipeline.py -v` all pass. Query "  What  IS   Photosynthesis?? " normalizes to "what is photosynthesis".

---

## Phase 4: User Story 2 — LLM-Powered Response Generation (Priority: P1)

**Goal**: Generate grounded natural language answers from retrieved context via Groq LLM API, with confidence scoring and fallback

**Independent Test**: Provide a factual question + retrieved passages → get coherent answer with citations. Provide out-of-domain question → get fallback response with low confidence. Update template file → next query uses new template.

### Tests for User Story 2

- [x] T018 [P] [US2] Create unit tests in tests/unit/test_llm_client.py — test GroqLLMClient.generate() with: mocked httpx response (success, 429 rate limit, 500 server error, timeout), verify retry logic, verify Authorization header, verify BaseLLMClient ABC contract
- [x] T019 [P] [US2] Create unit tests in tests/unit/test_prompt_builder.py — test build_qa_prompt() with: context chunks injected, conversation history included, missing fields handled; test build_system_prompt(); test hot-reload by modifying template file mtime
- [x] T020 [P] [US2] Create unit tests in tests/unit/test_validator.py — test validate() with: high retrieval scores + high overlap → high confidence, low scores → low confidence, empty context → near-zero confidence, threshold boundary cases
- [x] T021 [P] [US2] Create unit tests in tests/unit/test_fallback.py — test get_fallback_response() returns non-empty string, includes query context

### Implementation for User Story 2

- [x] T022 [P] [US2] Implement BaseLLMClient ABC and GroqLLMClient in src/mrag/generation/llm_client.py — BaseLLMClient with abstract async generate(prompt, system_prompt, temperature, max_tokens) → str; GroqLLMClient uses httpx.AsyncClient, POST to {api_url}/chat/completions, exponential backoff retry (max_retries, timeout from config), structured logging, raises ResponseGenerationError on failure
- [x] T023 [P] [US2] Implement PromptBuilder in src/mrag/generation/prompt_builder.py — __init__(templates_dir), Jinja2 Environment with FileSystemLoader, build_qa_prompt(query, context_chunks, conversation_history) and build_system_prompt(); hot-reload via mtime check on template files; structured logging
- [x] T024 [US2] Implement ResponseValidator in src/mrag/generation/validator.py — validate(response_text, context_chunks, retrieval_scores) computes confidence = alpha * mean(retrieval_scores) + (1-alpha) * tfidf_overlap(response_text, context); returns ValidationResult; uses sklearn TfidfVectorizer for overlap computation
- [x] T025 [US2] Implement FallbackHandler in src/mrag/generation/fallback.py — get_fallback_response(query) returns canned fallback message indicating insufficient information; loads from fallback_prompt.j2 template
- [x] T026 [US2] Implement GenerationPipeline in src/mrag/generation/pipeline.py — __init__(llm_client, prompt_builder, validator, fallback_handler), async generate_answer(query, retrieval_results, conversation_history) orchestrates: build prompt → call LLM → validate → return GeneratedResponse or fallback; structured logging; depends on T022-T025
- [x] T027 [US2] Update src/mrag/generation/__init__.py with public exports: BaseLLMClient, GroqLLMClient, PromptBuilder, ResponseValidator, FallbackHandler, GenerationPipeline, GeneratedResponse, ValidationResult, SourceCitation

**Checkpoint**: `pytest tests/unit/test_llm_client.py tests/unit/test_prompt_builder.py tests/unit/test_validator.py tests/unit/test_fallback.py -v` all pass. Mocked LLM calls produce validated responses. Fallback triggers on low confidence.

---

## Phase 5: User Story 3 — Response Caching for Repeated Queries (Priority: P2)

**Goal**: LRU embedding cache and TTL response cache so repeated queries skip re-computation

**Independent Test**: Send same query twice → second response in <50ms with cache_hit=True. Wait past TTL → cache miss on next request.

### Tests for User Story 3

- [x] T028 [P] [US3] Create unit tests in tests/unit/test_embedding_cache.py — test get/put, LRU eviction at max_size, invalidate, clear, stats (hits/misses/evictions)
- [x] T029 [P] [US3] Create unit tests in tests/unit/test_response_cache.py — test get/put, TTL expiration (mock time), max_size eviction, invalidate, clear, stats (hits/misses/expirations)

### Implementation for User Story 3

- [x] T030 [P] [US3] Implement EmbeddingCache in src/mrag/cache/embedding_cache.py — OrderedDict-based LRU, __init__(max_size), get(query_hash) → np.ndarray | None, put(query_hash, vector), invalidate(query_hash), clear(), size property, stats property tracking hits/misses/evictions; structured logging
- [x] T031 [P] [US3] Implement ResponseCache in src/mrag/cache/response_cache.py — dict with (GeneratedResponse, expires_at) tuples, __init__(max_size, default_ttl), get(query_hash) returns None if expired (lazy expiration), put(query_hash, response, ttl), invalidate, clear, size, stats; structured logging
- [x] T032 [US3] Update src/mrag/cache/__init__.py with public exports: EmbeddingCache, ResponseCache, RequestMetrics

**Checkpoint**: `pytest tests/unit/test_embedding_cache.py tests/unit/test_response_cache.py -v` all pass. LRU evicts correctly. TTL expires correctly.

---

## Phase 6: User Story 4 — Batch Query Processing (Priority: P2)

**Goal**: Batch-process multiple queries with optimized throughput for evaluation and benchmarking

**Independent Test**: Submit 100 queries as a batch → throughput at least 3x sequential. One failed query doesn't crash the batch.

### Tests for User Story 4

- [x] T033 [P] [US4] Create unit tests in tests/unit/test_batch_processor.py — test process_batch() with: multiple queries processed, empty list returns empty, single query failure doesn't crash batch (logged), retrieval_only mode returns RetrievalResults; mock retriever and generation pipeline

### Implementation for User Story 4

- [x] T034 [US4] Implement BatchProcessor in src/mrag/cache/batch_processor.py — __init__(retriever, generation_pipeline, batch_size=64), async process_batch(queries, retrieval_only=False): batch-embed all queries via EmbeddingEncoder.encode(), batch-search via FAISS, optionally generate responses (sequential LLM calls); per-query error handling with logging; structured logging for batch progress
- [x] T035 [US4] Update src/mrag/cache/__init__.py to add BatchProcessor export

**Checkpoint**: `pytest tests/unit/test_batch_processor.py -v` passes. Batch of queries processed with error isolation.

---

## Phase 7: User Story 5 — Performance Metrics Collection (Priority: P3)

**Goal**: Collect per-request timing metrics and provide aggregate statistics (p50/p95/p99)

**Independent Test**: Process 10 queries → each has metrics for all stages. Request summary → get percentile latencies.

### Tests for User Story 5

- [x] T036 [P] [US5] Create unit tests in tests/unit/test_metrics.py — test start_timer/stop_timer returns ms, record(RequestMetrics), get_summary() computes p50/p95/p99 for each field, cache_hit_rate computed correctly, reset() clears, request_count property

### Implementation for User Story 5

- [x] T037 [US5] Implement MetricsCollector in src/mrag/cache/metrics.py — start_timer(label)/stop_timer(label) using time.perf_counter_ns(), record(RequestMetrics) appends to in-memory list, get_summary() computes p50/p95/p99 via numpy.percentile for each numeric field + cache_hit_rate, reset(), request_count property; structured logging
- [x] T038 [US5] Update src/mrag/cache/__init__.py to add MetricsCollector export

**Checkpoint**: `pytest tests/unit/test_metrics.py -v` passes. Percentile calculations verified.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Integration, cache/metrics wiring into existing pipelines, and end-to-end validation

- [x] T039 Integrate EmbeddingCache into retrieval flow — update src/mrag/retrieval/retriever.py to accept optional EmbeddingCache, check cache before calling encoder.encode_single(), store result on miss
- [x] T040 Integrate ResponseCache and MetricsCollector into generation flow — create src/mrag/pipeline.py (top-level orchestrator): accepts QueryPipeline, RetrieverService, GenerationPipeline, EmbeddingCache, ResponseCache, MetricsCollector; wires cache checks and timing around each stage; returns GeneratedResponse
- [x] T041 [P] Create integration test in tests/integration/test_query_integration.py — test full query pipeline: raw input → normalized → contextualized → expanded → ProcessedQuery; uses real QueryPreprocessor, mocked retriever for expander
- [x] T042 [P] Create integration test in tests/integration/test_generation_integration.py — test generation pipeline end-to-end with mocked LLM client: query + retrieval results → prompt built → LLM called → validated → response or fallback; test template hot-reload
- [x] T043 Create end-to-end integration test in tests/integration/test_phase2_e2e.py — test full Phase 2 pipeline: raw query → query processing → retrieval (mocked FAISS) → generation (mocked LLM) → response with metrics; test cache hit on second identical query; test fallback on low-confidence
- [x] T044 Run black and ruff on all new files, fix any formatting/linting violations
- [x] T045 Run full test suite: `pytest tests/ -v --cov=mrag` — verify all Phase 1 and Phase 2 tests pass with no regressions

**Checkpoint**: End of Phase 2. Full pipeline with query processing, generation, caching, and metrics. `make test && make lint` passes. Phase 2 exit criteria met.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup (T001-T002 for config, T003-T005 for templates)
- **US1 Query Processing (Phase 3)**: Depends on Foundational (T006 for query models)
- **US2 Response Generation (Phase 4)**: Depends on Foundational (T007 for generation models, T008 for RequestMetrics)
- **US3 Caching (Phase 5)**: Depends on Foundational (T008 for RequestMetrics model)
- **US4 Batch Processing (Phase 6)**: Depends on US1 + US2 (needs retriever and generation pipeline)
- **US5 Metrics (Phase 7)**: Depends on Foundational (T008 for RequestMetrics model)
- **Polish (Phase 8)**: Depends on US1 through US5 completion

### User Story Dependencies

- **US1 (P1)**: Independent after Foundational — no other story dependencies
- **US2 (P1)**: Independent after Foundational — no dependency on US1 (receives retrieval results as input)
- **US3 (P2)**: Independent after Foundational — caches are standalone data structures
- **US4 (P2)**: Depends on US1 (QueryPipeline) and US2 (GenerationPipeline) being available for batch orchestration
- **US5 (P3)**: Independent after Foundational — metrics collector is standalone

### Parallel Opportunities

After Foundational completes, **US1, US2, US3, and US5 can all start in parallel** (independent modules, different files). US4 must wait for US1+US2.

### Within Each User Story

- Tests written first → verify they fail
- Models before services (already in Foundational)
- Core implementation before pipeline orchestration
- Commit after each task

---

## Parallel Example: After Foundational

```
# These 4 streams can run in parallel:
Stream A (US1): T009-T012 tests → T013-T017 implementation
Stream B (US2): T018-T021 tests → T022-T027 implementation
Stream C (US3): T028-T029 tests → T030-T032 implementation
Stream D (US5): T036 tests → T037-T038 implementation

# Then sequentially:
US4: T033 test → T034-T035 implementation (needs US1+US2)
Polish: T039-T045 (needs all stories)
```

---

## Implementation Strategy

### MVP First (US1 + US2)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: US1 — Query Processing
4. Complete Phase 4: US2 — Response Generation
5. **STOP and VALIDATE**: Query → preprocess → retrieve → generate → answer works end-to-end
6. This is the functional MVP — users can ask questions and get LLM-generated answers

### Incremental Delivery

1. Setup + Foundational → infrastructure ready
2. US1 (Query Processing) → normalized/expanded queries improve retrieval
3. US2 (Response Generation) → full Q&A pipeline functional (**MVP!**)
4. US3 (Caching) → repeated queries served instantly, cost savings
5. US4 (Batch Processing) → evaluation workloads unblocked
6. US5 (Metrics) → observability for production readiness
7. Polish → integration wiring, e2e tests, lint pass

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Constitution Article VI mandates tests for every module — tests included in each story
- All config values externalized per Article IX — no magic numbers
- Structured logging (structlog) in every module per Article IX — no print statements
- All Pydantic models use type hints per Article IX
- Commit after each task or logical group
