# Implementation Plan: Phase 2 RAG Pipeline — Query Processing, Response Generation & Caching

**Branch**: `003-phase2-rag-pipeline` | **Date**: 2026-04-08 | **Spec**: specs/003-phase2-rag-pipeline/spec.md
**Input**: Feature specification from `/specs/003-phase2-rag-pipeline/spec.md`
**Constitution Version**: 1.0.0

## Summary

Phase 2 extends the Phase 1 RAG foundation (data processing, embeddings, FAISS index, basic retrieval) with three capabilities: intelligent query processing (normalization, expansion, multi-turn context), LLM-powered response generation (Groq API via abstract client, Jinja2 templates, confidence scoring, fallback), and performance optimization (LRU/TTL caching, batch processing, per-request metrics). All computation targets Apple Silicon CPU — no CUDA dependencies.

## Technical Context

**Language/Version**: Python 3.10+ (conda environment `mrag`)
**Primary Dependencies**: sentence-transformers 4.1.0, faiss-cpu 1.11.0, httpx 0.28.1, Jinja2, Pydantic 2.11.3, structlog 25.2.0, NumPy 2.2.6
**Storage**: FAISS index files (.faiss) + JSON metadata files (no database in Phase 2)
**Testing**: pytest 8.3.5, pytest-asyncio 0.26.0, pytest-cov 6.1.1
**Target Platform**: macOS Apple Silicon (M-series), CPU-only
**Project Type**: Library (API layer deferred to Phase 3)
**Performance Goals**: <10ms query preprocessing, <200ms retrieval, <3s e2e p95, <50ms cache hits
**Constraints**: No CUDA/NVIDIA GPU, Groq-compatible LLM API, multilingual UTF-8 throughout
**Scale/Scope**: ~86K Q&A pairs, ~300K+ chunks in FAISS index

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Article | Requirement | Status | Notes |
|---------|-------------|--------|-------|
| I — Modular Architecture | Each component is an independent module | PASS | Three new modules: `query/`, `generation/`, `cache/` with explicit I/O contracts |
| II — Data Integrity | Validated preprocessing pipeline | PASS | Inherits Phase 1 pipeline; query normalization adds validation at input boundary |
| III — Multilingual-First | Unicode normalization, multilingual models | PASS | NFC normalization in preprocessor; multilingual embedding model from Phase 1 |
| IV — Retrieval Quality > Speed | Ranking, expansion, configurable top-K | PASS | Query expansion via pseudo-relevance feedback; accuracy over speed |
| V — LLM as Replaceable Contract | BaseLLMClient ABC, externalized templates | PASS | Abstract client + GroqLLMClient; Jinja2 templates from filesystem |
| VI — Testing | Unit + integration tests per module | PASS | Tests planned for every module; evaluation metrics deferred to Phase 3 |
| VII — API Standards | FastAPI, Pydantic validation | DEFERRED | API layer is Phase 3; internal interfaces use Pydantic models |
| VIII — Caching Discipline | LRU/TTL, batch, metrics | PASS | Dedicated cache module with LRU + TTL + metrics collector |
| IX — Code Quality | Type hints, black, ruff, structured logging | PASS | All existing standards maintained |
| X — Documentation Separation | Spec = WHAT, Plan = HOW | PASS | Spec is technology-agnostic; plan contains all tech decisions |

No violations. Article VII deferred to Phase 3 with documented justification.

## Project Structure

### Documentation (this feature)

```text
specs/003-phase2-rag-pipeline/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

```text
src/mrag/
├── query/                       # Feature 004 — Query Processing
│   ├── __init__.py
│   ├── preprocessor.py          # QueryPreprocessor: normalize, clean
│   ├── expander.py              # QueryExpander: pseudo-relevance feedback
│   ├── context_manager.py       # ConversationContextManager: history prepend
│   ├── models.py                # ProcessedQuery, ExpandedQuery, ConversationTurn
│   └── pipeline.py              # QueryPipeline: preprocess → expand → contextualize
│
├── generation/                  # Feature 005 — Response Generation
│   ├── __init__.py
│   ├── llm_client.py            # BaseLLMClient ABC + GroqLLMClient (httpx async)
│   ├── prompt_builder.py        # PromptBuilder: Jinja2 template loading & rendering
│   ├── validator.py             # ResponseValidator: confidence scoring
│   ├── fallback.py              # FallbackHandler: low-confidence responses
│   ├── models.py                # GeneratedResponse, ValidationResult
│   └── pipeline.py              # GenerationPipeline: query → context → prompt → LLM → validate
│
├── cache/                       # Feature 006 — Caching & Performance
│   ├── __init__.py
│   ├── embedding_cache.py       # EmbeddingCache: LRU cache for query embeddings
│   ├── response_cache.py        # ResponseCache: TTL cache for full responses
│   ├── batch_processor.py       # BatchProcessor: batched query processing
│   └── metrics.py               # MetricsCollector: per-request timing & aggregation
│
├── retrieval/                   # Existing Phase 1 (updated for cache/metrics integration)
│   ├── retriever.py             # RetrieverService — add cache + metrics hooks
│   ├── ranking.py
│   └── models.py
│
├── config.py                    # Existing — add new Phase 2 config fields
├── exceptions.py                # Existing — already has Phase 2 exceptions
└── logging.py                   # Existing

prompts/templates/               # Jinja2 prompt templates
├── qa_prompt.j2                 # Main Q&A prompt
├── system_prompt.j2             # System instruction
└── fallback_prompt.j2           # Fallback response template

tests/
├── unit/
│   ├── test_preprocessor.py
│   ├── test_expander.py
│   ├── test_context_manager.py
│   ├── test_query_pipeline.py
│   ├── test_llm_client.py
│   ├── test_prompt_builder.py
│   ├── test_validator.py
│   ├── test_fallback.py
│   ├── test_embedding_cache.py
│   ├── test_response_cache.py
│   ├── test_batch_processor.py
│   └── test_metrics.py
└── integration/
    ├── test_query_integration.py
    ├── test_generation_integration.py
    └── test_phase2_e2e.py
```

**Structure Decision**: Extends the existing `src/mrag/` flat namespace established in Phase 0. Three new modules (`query/`, `generation/`, `cache/`) follow the same pattern as existing modules (`data/`, `embeddings/`, `retrieval/`). Prompt templates live under `prompts/templates/` as established in Phase 0 layout.

## Architecture

### Data Flow

```
User Query (raw text)
    │
    ▼
[QueryPreprocessor] → normalize unicode (NFC), collapse whitespace, lowercase
    │
    ▼
[ConversationContextManager] → prepend recent history (sliding window, heuristic)
    │
    ▼
[QueryExpander] → embed → retrieve top-3 → extract key terms → append
    │
    ▼
[EmbeddingCache] ──cache hit──→ [cached vector]
    │ miss                              │
    ▼                                   ▼
[EmbeddingEncoder] → query vector ──────┘
    │
    ▼
[ResponseCache] ──cache hit──→ [cached response] → return
    │ miss
    ▼
[RetrieverService] → FAISS search → re-rank → filter
    │
    ▼
[PromptBuilder] → load Jinja2 template + inject context + history
    │
    ▼
[GroqLLMClient] → API call → raw LLM response
    │
    ▼
[ResponseValidator] → confidence score (retrieval scores + TF-IDF overlap)
    │
    ├── confidence ≥ threshold → GeneratedResponse
    └── confidence < threshold → [FallbackHandler] → fallback response

[MetricsCollector] ← records timing at each stage
```

### Key Technical Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Query normalization | `unicodedata.normalize("NFC")` + regex | Per Article III; handles multilingual input correctly |
| Context resolution | History prepend (heuristic) | Clarified in spec: no extra LLM call, keeps <10ms |
| Query expansion | Pseudo-relevance feedback (top-3 retrieval → TF-IDF term extraction) | Per Article IV: evaluate before enabling; no ML dependency |
| LLM client | `httpx.AsyncClient` to Groq OpenAI-compatible endpoint | Per Article V: swappable via BaseLLMClient ABC |
| Prompt templates | Jinja2 loaded from `prompts/templates/` | Per Article V: externalized, hot-reloadable via file mtime check |
| Confidence scoring | Weighted avg retrieval scores + TF-IDF overlap (answer vs context) | Simple, no extra model; per Article V |
| Confidence threshold | 0.3 default (configurable via Settings) | Calibrated in evaluation; per Article V |
| Embedding cache | `collections.OrderedDict` LRU, configurable max_size | Per Article VIII; O(1) get/put |
| Response cache | `dict` with TTL metadata, keyed by normalized query hash | Clarified in spec: exact match on normalized hash |
| Cache hash | `hashlib.md5(normalized_query.encode()).hexdigest()` | Deterministic, fast, sufficient for cache keys |
| Batch processing | Leverage existing `EmbeddingEncoder.encode()` batch + FAISS batch search | Per Article VIII; 3x+ throughput vs sequential |
| Metrics | `time.perf_counter_ns()` with in-memory accumulator | Per Article VIII; <5ms overhead; JSON export |
| LLM retry | Exponential backoff, max 3 retries, configurable timeout (30s default) | Per FR-015; httpx built-in transport retry |
| Apple Silicon | `faiss-cpu` (uses Apple Accelerate via NumPy), no CUDA imports | Per FR-014; verified with existing Phase 1 |

### New Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| Jinja2 | 3.1.x | Prompt template rendering |
| httpx | 0.28.1 | Already in pyproject.toml; async HTTP for LLM API |

Jinja2 needs to be added to `pyproject.toml`. All other dependencies are already present.

### Config Additions

New fields to add to `Settings` in `src/mrag/config.py`:

```python
# Query Processing
query_expansion_enabled: bool = True
query_expansion_top_n: int = 3
conversation_history_max_turns: int = 5

# Generation
confidence_threshold: float = 0.3
llm_timeout_seconds: int = 30
llm_max_retries: int = 3
```

Existing fields already cover: `llm_api_url`, `llm_api_key`, `llm_model_name`, `llm_temperature`, `llm_max_tokens`, `cache_ttl_seconds`, `cache_max_size`, `prompts_dir`.
