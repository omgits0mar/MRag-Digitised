"""Unit tests for mrag.cache.embedding_cache.EmbeddingCache."""

from __future__ import annotations

import numpy as np
import pytest

from mrag.cache.embedding_cache import EmbeddingCache


class TestEmbeddingCache:
    def test_get_missing_returns_none(self) -> None:
        cache = EmbeddingCache(max_size=2)
        assert cache.get("unknown") is None
        assert cache.stats["misses"] == 1

    def test_put_and_get_roundtrip(self) -> None:
        cache = EmbeddingCache(max_size=2)
        vec = np.arange(4, dtype=np.float32)
        cache.put("k1", vec)
        got = cache.get("k1")
        assert got is not None
        np.testing.assert_array_equal(got, vec)
        assert cache.stats["hits"] == 1

    def test_lru_eviction_at_capacity(self) -> None:
        cache = EmbeddingCache(max_size=2)
        cache.put("k1", np.array([1.0], dtype=np.float32))
        cache.put("k2", np.array([2.0], dtype=np.float32))
        # Access k1 → becomes MRU; k2 is now LRU.
        _ = cache.get("k1")
        cache.put("k3", np.array([3.0], dtype=np.float32))
        assert cache.get("k2") is None  # evicted
        assert cache.get("k1") is not None
        assert cache.get("k3") is not None
        assert cache.stats["evictions"] == 1

    def test_invalidate(self) -> None:
        cache = EmbeddingCache(max_size=2)
        cache.put("k1", np.array([1.0], dtype=np.float32))
        assert cache.invalidate("k1") is True
        assert cache.invalidate("k1") is False
        assert cache.get("k1") is None

    def test_clear(self) -> None:
        cache = EmbeddingCache(max_size=2)
        cache.put("k1", np.array([1.0], dtype=np.float32))
        cache.put("k2", np.array([2.0], dtype=np.float32))
        cache.clear()
        assert cache.size == 0

    def test_update_existing_key_no_eviction(self) -> None:
        cache = EmbeddingCache(max_size=2)
        cache.put("k1", np.array([1.0], dtype=np.float32))
        cache.put("k2", np.array([2.0], dtype=np.float32))
        cache.put("k1", np.array([99.0], dtype=np.float32))
        assert cache.stats["evictions"] == 0
        assert cache.get("k1")[0] == 99.0

    def test_invalid_max_size_raises(self) -> None:
        with pytest.raises(ValueError):
            EmbeddingCache(max_size=0)
