# Data Model: Project Foundation & Environment Setup

**Branch**: `001-project-foundation` | **Date**: 2026-04-06
**Spec**: `specs/001-project-foundation/spec.md`

---

## Entity: Settings

The centralized, immutable configuration object loaded once at startup.

| Field | Type | Default | Required | Sensitive | Description |
|---|---|---|---|---|---|
| `app_name` | `str` | `"mrag"` | No | No | Application name used in logging and metadata |
| `app_version` | `str` | `"0.1.0"` | No | No | Application version (mirrors `__version__`) |
| `debug` | `bool` | `False` | No | No | Enable debug mode (verbose logging) |
| `log_level` | `str` | `"INFO"` | No | No | Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL |
| `embedding_model_name` | `str` | `"paraphrase-multilingual-MiniLM-L12-v2"` | No | No | Sentence Transformer model for embeddings |
| `embedding_dimension` | `int` | `384` | No | No | Embedding vector dimension (must match model) |
| `chunk_size` | `int` | `512` | No | No | Text chunk size in characters for data processing |
| `chunk_overlap` | `int` | `50` | No | No | Overlap between adjacent chunks in characters |
| `top_k` | `int` | `5` | No | No | Number of results to retrieve per query |
| `faiss_index_type` | `str` | `"Flat"` | No | No | FAISS index type: Flat, IVF, HNSW |
| `llm_api_url` | `str` | `"https://api.groq.com/openai/v1"` | No | No | LLM API endpoint URL |
| `llm_api_key` | `SecretStr` | — | Yes | **Yes** | LLM API key (redacted in logs/repr) |
| `llm_model_name` | `str` | `"llama3-8b-8192"` | No | No | LLM model identifier |
| `llm_temperature` | `float` | `0.1` | No | No | LLM generation temperature |
| `llm_max_tokens` | `int` | `1024` | No | No | Maximum tokens in LLM response |
| `database_url` | `SecretStr` | `"sqlite:///mrag.db"` | No | **Yes** | SQLAlchemy database connection URL |
| `cache_ttl_seconds` | `int` | `3600` | No | No | Cache TTL in seconds |
| `cache_max_size` | `int` | `1000` | No | No | Maximum number of cached entries |
| `data_dir` | `str` | `"data"` | No | No | Base directory for data files |
| `prompts_dir` | `str` | `"prompts/templates"` | No | No | Directory for prompt templates |

**Validation Rules**:
- `log_level` must be one of: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
- `chunk_size` must be > 0
- `chunk_overlap` must be >= 0 and < `chunk_size`
- `top_k` must be >= 1
- `embedding_dimension` must be > 0
- `llm_temperature` must be >= 0.0 and <= 2.0
- `llm_max_tokens` must be > 0
- `cache_ttl_seconds` must be > 0
- `cache_max_size` must be > 0
- `faiss_index_type` must be one of: `Flat`, `IVF`, `HNSW`

**Lifecycle**: Created once at application startup. Immutable after creation (frozen). Destroyed at process exit. Changes require restart.

**Sensitive Fields**: `llm_api_key`, `database_url` — must use `SecretStr` type, redacted in `repr()`, `str()`, and log output.

---

## Entity: Logger

A structured logging instance bound to a module name.

| Field | Type | Description |
|---|---|---|
| `module_name` | `str` | The `__name__` of the calling module (e.g., `mrag.config`, `mrag.retrieval`) |
| `bound_context` | `dict[str, Any]` | Optional key-value pairs bound to every log entry from this logger |

**Output Schema** (each log entry is one JSON object):

```json
{
  "timestamp": "2026-04-06T12:00:00.000Z",
  "level": "INFO",
  "module": "mrag.config",
  "event": "Configuration loaded successfully",
  "context_key": "context_value"
}
```

**Required Fields**: `timestamp` (ISO 8601), `level`, `module`, `event`.
**Optional Fields**: Any additional key-value pairs bound or passed at log time.

**Redaction**: Before JSON serialization, a processor scans all context fields against a set of sensitive key patterns (`api_key`, `secret`, `password`, `token`, `credential`, `database_url`). Matching values are replaced with `"***"`.

---

## Entity: Exception Hierarchy

A tree of exception classes for uniform error handling.

```
Exception
└── MRAGError (base project exception)
    ├── DataProcessingError
    ├── EmbeddingError
    ├── RetrievalError
    ├── QueryProcessingError
    ├── ResponseGenerationError
    ├── CacheError
    ├── APIError
    ├── DatabaseError
    └── EvaluationError
```

| Field | Type | Description |
|---|---|---|
| `message` | `str` | Human-readable error description |
| `detail` | `dict[str, Any] \| None` | Optional structured error context for debugging/API responses |

**Relationships**:
- All module exceptions inherit from `MRAGError`.
- `MRAGError` inherits from Python's `Exception` (not `BaseException`).
- Module-specific sub-exceptions (e.g., `ChunkingError(DataProcessingError)`) are deferred to each module's feature implementation.

---

## Entity Relationships

```
Settings (1) ──reads──> Logger (*)     : Logger reads log_level from Settings
Settings (1) ──reads──> Module (*)     : All modules read config from Settings
Logger   (1) ──uses───> Redaction (1)  : Logger processor redacts sensitive Settings fields
Module   (*) ──raises─> Exception (*)  : Modules raise module-specific exceptions
```
