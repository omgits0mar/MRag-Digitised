"""LRU cache for query embedding vectors.

An OrderedDict-based implementation that supports O(1) get/put with
least-recently-used eviction. Tracks hit / miss / eviction counts for
observability (wired into ``MetricsCollector``).
"""

from __future__ import annotations

from collections import OrderedDict

import numpy as np
import structlog

logger = structlog.get_logger(__name__)


class EmbeddingCache:
    """Bounded LRU cache keyed by query hash → embedding vector.

    Args:
        max_size: Maximum number of entries before LRU eviction.
    """

    def __init__(self, max_size: int = 1000) -> None:
        if max_size < 1:
            raise ValueError("max_size must be >= 1")
        self._max_size = max_size
        self._store: OrderedDict[str, np.ndarray] = OrderedDict()
        self._hits = 0
        self._misses = 0
        self._evictions = 0

    def get(self, query_hash: str) -> np.ndarray | None:
        """Return the cached vector or ``None`` on miss (promotes to MRU)."""
        vec = self._store.get(query_hash)
        if vec is None:
            self._misses += 1
            logger.debug("embedding_cache_miss", key=query_hash[:8])
            return None
        self._store.move_to_end(query_hash)
        self._hits += 1
        logger.debug("embedding_cache_hit", key=query_hash[:8])
        return vec

    def put(self, query_hash: str, vector: np.ndarray) -> None:
        """Insert or update an entry; evicts the LRU item if at capacity."""
        if query_hash in self._store:
            self._store.move_to_end(query_hash)
            self._store[query_hash] = vector
            return

        if len(self._store) >= self._max_size:
            evicted_key, _ = self._store.popitem(last=False)
            self._evictions += 1
            logger.debug("embedding_cache_evict", key=evicted_key[:8])

        self._store[query_hash] = vector

    def invalidate(self, query_hash: str) -> bool:
        """Remove a specific entry. Returns ``True`` if it existed."""
        if query_hash in self._store:
            del self._store[query_hash]
            return True
        return False

    def clear(self) -> None:
        """Remove all entries (stats are preserved)."""
        self._store.clear()
        logger.debug("embedding_cache_cleared")

    @property
    def size(self) -> int:
        return len(self._store)

    @property
    def stats(self) -> dict[str, int]:
        return {
            "hits": self._hits,
            "misses": self._misses,
            "evictions": self._evictions,
            "size": self.size,
        }
