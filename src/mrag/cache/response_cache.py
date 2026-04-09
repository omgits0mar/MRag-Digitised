"""TTL-based response cache keyed by the normalized-query hash.

Uses a plain dict with ``(response, expires_at)`` tuples. Expired entries
are evicted lazily on access. Capacity enforcement drops the oldest
entry by insertion order when ``put`` would exceed ``max_size``.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from mrag.generation.models import GeneratedResponse

logger = structlog.get_logger(__name__)


class ResponseCache:
    """Bounded TTL cache of ``GeneratedResponse`` objects.

    Args:
        max_size: Maximum number of entries retained.
        default_ttl: Default TTL in seconds applied when ``put`` is
            called without an explicit ``ttl``.
    """

    def __init__(self, max_size: int = 1000, default_ttl: int = 3600) -> None:
        if max_size < 1:
            raise ValueError("max_size must be >= 1")
        if default_ttl < 1:
            raise ValueError("default_ttl must be >= 1")
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._store: dict[str, tuple[GeneratedResponse, float]] = {}
        self._hits = 0
        self._misses = 0
        self._expirations = 0

    def get(self, query_hash: str) -> GeneratedResponse | None:
        """Return the cached response, or ``None`` if missing / expired."""
        entry = self._store.get(query_hash)
        if entry is None:
            self._misses += 1
            logger.debug("response_cache_miss", key=query_hash[:8])
            return None

        response, expires_at = entry
        now = time.time()
        if now >= expires_at:
            del self._store[query_hash]
            self._expirations += 1
            self._misses += 1
            logger.debug("response_cache_expired", key=query_hash[:8])
            return None

        self._hits += 1
        logger.debug("response_cache_hit", key=query_hash[:8])
        return response

    def put(
        self,
        query_hash: str,
        response: GeneratedResponse,
        ttl: int | None = None,
    ) -> None:
        """Store ``response`` with TTL; evicts oldest entry if at capacity."""
        effective_ttl = ttl if ttl is not None else self._default_ttl
        expires_at = time.time() + effective_ttl

        # If updating, just overwrite in place without eviction.
        if query_hash in self._store:
            self._store[query_hash] = (response, expires_at)
            return

        if len(self._store) >= self._max_size:
            # Evict oldest insertion (dicts are ordered since Python 3.7).
            oldest_key = next(iter(self._store))
            del self._store[oldest_key]
            logger.debug("response_cache_evict", key=oldest_key[:8])

        self._store[query_hash] = (response, expires_at)

    def invalidate(self, query_hash: str) -> bool:
        if query_hash in self._store:
            del self._store[query_hash]
            return True
        return False

    def clear(self) -> None:
        self._store.clear()
        logger.debug("response_cache_cleared")

    @property
    def size(self) -> int:
        """Current number of non-expired entries (prunes expired lazily)."""
        now = time.time()
        expired = [k for k, (_, exp) in self._store.items() if now >= exp]
        for k in expired:
            del self._store[k]
            self._expirations += 1
        return len(self._store)

    @property
    def stats(self) -> dict[str, int]:
        return {
            "hits": self._hits,
            "misses": self._misses,
            "expirations": self._expirations,
            "size": len(self._store),
        }
