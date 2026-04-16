# Research: Phase 2 RAG Pipeline

**Branch**: `003-phase2-rag-pipeline` | **Date**: 2026-04-08

## R1: Pseudo-Relevance Feedback for Query Expansion

**Decision**: Use pseudo-relevance feedback (PRF) with top-3 initial retrieval results and TF-IDF term extraction to expand short/ambiguous queries.

**Rationale**: PRF is a well-established IR technique that doesn't require additional ML models or training data. It leverages the existing retrieval pipeline: embed the raw query, retrieve top-N candidates, extract high-weight terms from those candidates via TF-IDF, and append them to the original query for a second retrieval pass. This improves recall without adding model dependencies.

**Alternatives considered**:
- **WordNet/synonym expansion**: Limited to English, no multilingual support, requires NLTK data.
- **LLM-based expansion**: Adds latency and cost (extra API call per query); violates the <10ms preprocessing target.
- **Embedding-space nearest-neighbor terms**: Requires a separate term-level embedding index; adds complexity.

**Key parameters**: `top_n=3` (number of PRF documents), `max_expansion_terms=5` (terms extracted per PRF round), `expansion_weight=0.3` (relative weight vs original query terms).

---

## R2: Groq API Integration Pattern

**Decision**: Use `httpx.AsyncClient` with the OpenAI-compatible endpoint format (`/v1/chat/completions`). Wrap in a `BaseLLMClient` ABC with `generate()` as the core method.

**Rationale**: Groq exposes an OpenAI-compatible API, so the client implementation is straightforward. `httpx` is already a project dependency (used for async HTTP). The ABC pattern allows swapping providers (OpenAI, Anthropic, local models) by implementing the same interface.

**Alternatives considered**:
- **`openai` Python SDK**: Would work with Groq's compatible endpoint, but adds a dependency and couples to OpenAI's SDK release cycle.
- **`requests`**: Synchronous; doesn't fit the async pipeline architecture.
- **`aiohttp`**: Viable but `httpx` is already in the project and has a cleaner API.

**API contract**:
- Endpoint: `{llm_api_url}/chat/completions`
- Auth: `Authorization: Bearer {llm_api_key}`
- Model: configurable, default `llama3-8b-8192`
- Retry: exponential backoff, max 3 retries, 30s timeout

---

## R3: Confidence Scoring Strategy

**Decision**: Compute confidence as a weighted combination of retrieval score aggregation (mean of top-K cosine similarities) and answer-context TF-IDF overlap (proportion of answer n-grams found in retrieved context).

**Rationale**: This approach requires no additional ML model and provides a reasonable signal for answer groundedness. High retrieval scores + high term overlap = high confidence that the answer is derived from context rather than hallucinated.

**Alternatives considered**:
- **LLM self-evaluation**: Ask the LLM to rate its own confidence. Unreliable and adds latency/cost.
- **NLI-based entailment check**: Requires loading a separate NLI model (e.g., DeBERTa). Too heavy for Phase 2.
- **Retrieval score only**: Misses cases where the LLM ignores context and generates from parametric knowledge.

**Formula**: `confidence = alpha * mean_retrieval_score + (1 - alpha) * tfidf_overlap`, where `alpha=0.6` (configurable). Threshold default: `0.3`.

---

## R4: Jinja2 Template Hot-Reloading

**Decision**: Check file modification time (`os.path.getmtime()`) on each template load. Cache the compiled template alongside its mtime. Re-compile only when mtime changes.

**Rationale**: Simple, zero-dependency approach (Jinja2 is already needed for template rendering). Avoids filesystem watchers (platform-dependent, unnecessary complexity). The mtime check is <1ms overhead.

**Alternatives considered**:
- **`watchdog` file watcher**: Platform-dependent, adds a dependency, requires a background thread.
- **Reload on every request**: Slightly slower but simpler. Rejected because Jinja2 compilation has non-trivial cost for complex templates.
- **No hot-reload (restart required)**: Doesn't meet FR-006.

---

## R5: Apple Silicon / CPU-Only Considerations

**Decision**: All computation uses CPU paths. `faiss-cpu` leverages Apple's Accelerate framework through NumPy's BLAS backend. Sentence Transformers runs on CPU (PyTorch MPS backend available but not required).

**Rationale**: The existing Phase 1 pipeline already runs on Apple Silicon with `faiss-cpu`. No changes needed. PyTorch detects Apple Silicon and can optionally use MPS, but for embedding inference the CPU path is sufficient (model is small: 118M params).

**Alternatives considered**:
- **PyTorch MPS backend**: Could accelerate embedding inference, but sentence-transformers' `encode()` handles device selection internally. MPS support in sentence-transformers is experimental. CPU is reliable and meets latency targets.
- **CoreML conversion**: Possible for the embedding model but adds significant complexity. Deferred unless CPU performance proves insufficient.

**Verification**: `faiss-cpu` 1.11.0 is confirmed compatible with Apple Silicon ARM64 via conda-forge/pip.

---

## R6: LRU Cache Implementation

**Decision**: Use `collections.OrderedDict` for the LRU embedding cache. For the response TTL cache, use a plain `dict` with per-entry `(value, expiry_timestamp)` tuples and lazy expiration on access.

**Rationale**: Python's `OrderedDict` supports `move_to_end()` for O(1) LRU operations. The `functools.lru_cache` decorator is unsuitable because it caches function return values and doesn't support explicit invalidation or size introspection. A custom implementation gives full control over eviction, metrics integration, and thread safety.

**Alternatives considered**:
- **`functools.lru_cache`**: No invalidation API, no introspection, wraps functions rather than keyed storage.
- **`cachetools.LRUCache`**: Good library but adds a dependency for a simple data structure.
- **Redis**: Overkill for single-process in-memory caching; adds infrastructure dependency.

**Thread safety**: Not needed in Phase 2 (single-process, async but single-threaded event loop). Can add `threading.Lock` wrapper if needed later.
