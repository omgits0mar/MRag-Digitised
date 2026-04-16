# Contract: Exception Hierarchy

**Module**: `mrag.exceptions`
**Consumers**: All modules

---

## Interface

### `MRAGError(Exception)`

Base exception for all project-specific errors.

**Constructor**: `MRAGError(message: str, detail: dict[str, Any] | None = None)`

| Attribute | Type | Description |
|---|---|---|
| `message` | `str` | Human-readable error description |
| `detail` | `dict[str, Any] \| None` | Optional structured context for debugging/API error responses |

**Behavior**:
- `str(error)` returns `message`.
- `error.detail` provides structured context compatible with the API error schema.

### Module-Specific Exceptions

Each inherits from `MRAGError` with identical constructor signature:

| Exception Class | Module | Usage |
|---|---|---|
| `DataProcessingError` | `mrag.data` | Dataset loading, parsing, chunking failures |
| `EmbeddingError` | `mrag.embeddings` | Embedding model loading, inference failures |
| `RetrievalError` | `mrag.retrieval` | Vector search, index loading failures |
| `QueryProcessingError` | `mrag.query` | Query parsing, expansion failures |
| `ResponseGenerationError` | `mrag.generation` | LLM call failures, response validation |
| `CacheError` | `mrag.cache` | Cache read/write, invalidation failures |
| `APIError` | `mrag.api` | Request validation, endpoint failures |
| `DatabaseError` | `mrag.db` | Connection, query, migration failures |
| `EvaluationError` | `mrag.evaluation` | Metric computation, benchmark failures |

---

## Catching Contract

```python
from mrag.exceptions import MRAGError, RetrievalError

try:
    results = search(query)
except RetrievalError as e:
    # Catches only retrieval errors
    logger.error("Search failed", error=e.message, detail=e.detail)
except MRAGError as e:
    # Catches any project error
    logger.error("MRAG error", error=e.message)
```

---

## API Error Mapping

When exceptions reach the API layer, they map to the standard error response:

```json
{
  "error": "RetrievalError",
  "detail": "FAISS index not loaded",
  "status_code": 500
}
```
