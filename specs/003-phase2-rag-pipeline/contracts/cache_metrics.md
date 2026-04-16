# Contract: Caching & Metrics

**Module**: `src/mrag/cache/`

## EmbeddingCache

```python
class EmbeddingCache:
    def __init__(self, max_size: int = 1000) -> None: ...

    def get(self, query_hash: str) -> np.ndarray | None:
        """Retrieve cached embedding vector.

        Returns:
            Cached numpy array or None on miss.
        """

    def put(self, query_hash: str, vector: np.ndarray) -> None:
        """Store embedding vector. Evicts LRU entry if at capacity."""

    def invalidate(self, query_hash: str) -> bool:
        """Remove a specific entry. Returns True if found."""

    def clear(self) -> None:
        """Evict all entries."""

    @property
    def size(self) -> int:
        """Current number of cached entries."""

    @property
    def stats(self) -> dict[str, int]:
        """Return hits, misses, evictions counts."""
```

## ResponseCache

```python
class ResponseCache:
    def __init__(self, max_size: int = 1000, default_ttl: int = 3600) -> None: ...

    def get(self, query_hash: str) -> GeneratedResponse | None:
        """Retrieve cached response. Returns None if expired or missing."""

    def put(
        self, query_hash: str, response: GeneratedResponse, ttl: int | None = None
    ) -> None:
        """Store response with TTL. Evicts oldest if at capacity."""

    def invalidate(self, query_hash: str) -> bool:
        """Remove a specific entry."""

    def clear(self) -> None:
        """Evict all entries."""

    @property
    def size(self) -> int:
        """Current number of non-expired entries."""

    @property
    def stats(self) -> dict[str, int]:
        """Return hits, misses, expirations counts."""
```

## BatchProcessor

```python
class BatchProcessor:
    def __init__(
        self,
        retriever: RetrieverService,
        generation_pipeline: GenerationPipeline | None = None,
        batch_size: int = 64,
    ) -> None: ...

    async def process_batch(
        self,
        queries: list[str],
        retrieval_only: bool = False,
    ) -> list[GeneratedResponse | list[RetrievalResult]]:
        """Process multiple queries with batched operations.

        1. Batch-embed all queries
        2. Batch-search FAISS index
        3. Optionally generate responses (sequential LLM calls)

        Args:
            queries: List of query strings.
            retrieval_only: If True, skip generation and return retrieval results.

        Returns:
            List of responses or retrieval results, one per query.
            Failed queries return error responses (not raised).
        """
```

## MetricsCollector

```python
class MetricsCollector:
    def start_timer(self, label: str) -> None:
        """Start a named timer using perf_counter_ns."""

    def stop_timer(self, label: str) -> float:
        """Stop timer and return elapsed milliseconds."""

    def record(self, metrics: RequestMetrics) -> None:
        """Append a completed request's metrics to the accumulator."""

    def get_summary(self) -> dict[str, dict[str, float]]:
        """Compute p50, p95, p99 for each metric field.

        Returns:
            {
                "embedding_time_ms": {"p50": ..., "p95": ..., "p99": ...},
                "search_time_ms": {...},
                "llm_time_ms": {...},
                "total_time_ms": {...},
                "cache_hit_rate": float,
            }
        """

    def reset(self) -> None:
        """Clear accumulated metrics."""

    @property
    def request_count(self) -> int:
        """Total recorded requests."""
```
