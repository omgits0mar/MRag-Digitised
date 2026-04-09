"""Unit tests for mrag.cache.response_cache.ResponseCache."""

from __future__ import annotations

import pytest

from mrag.cache.models import RequestMetrics
from mrag.cache.response_cache import ResponseCache
from mrag.generation.models import GeneratedResponse


def _resp(answer: str = "answer") -> GeneratedResponse:
    return GeneratedResponse(
        query="q",
        answer=answer,
        confidence_score=0.9,
        is_fallback=False,
        sources=[],
        metrics=RequestMetrics(),
    )


class TestResponseCache:
    def test_put_and_get(self) -> None:
        cache = ResponseCache(max_size=4, default_ttl=60)
        cache.put("k1", _resp("hello"))
        got = cache.get("k1")
        assert got is not None
        assert got.answer == "hello"
        assert cache.stats["hits"] == 1

    def test_missing_returns_none(self) -> None:
        cache = ResponseCache(max_size=4, default_ttl=60)
        assert cache.get("missing") is None
        assert cache.stats["misses"] == 1

    def test_ttl_expiration(self, monkeypatch: pytest.MonkeyPatch) -> None:
        cache = ResponseCache(max_size=4, default_ttl=60)

        # Freeze time to T=0 for put.
        current = {"t": 1000.0}
        monkeypatch.setattr("mrag.cache.response_cache.time.time", lambda: current["t"])
        cache.put("k1", _resp(), ttl=10)

        # Advance past expiration.
        current["t"] = 1100.0
        assert cache.get("k1") is None
        assert cache.stats["expirations"] == 1

    def test_max_size_eviction_of_oldest(self) -> None:
        cache = ResponseCache(max_size=2, default_ttl=60)
        cache.put("k1", _resp("a"))
        cache.put("k2", _resp("b"))
        cache.put("k3", _resp("c"))
        assert cache.get("k1") is None  # evicted
        assert cache.get("k2") is not None
        assert cache.get("k3") is not None

    def test_invalidate(self) -> None:
        cache = ResponseCache(max_size=4, default_ttl=60)
        cache.put("k1", _resp())
        assert cache.invalidate("k1") is True
        assert cache.invalidate("k1") is False

    def test_clear(self) -> None:
        cache = ResponseCache(max_size=4, default_ttl=60)
        cache.put("k1", _resp())
        cache.clear()
        assert cache.size == 0

    def test_update_in_place(self) -> None:
        cache = ResponseCache(max_size=2, default_ttl=60)
        cache.put("k1", _resp("first"))
        cache.put("k2", _resp("second"))
        cache.put("k1", _resp("updated"))
        got = cache.get("k1")
        assert got is not None and got.answer == "updated"
        assert cache.get("k2") is not None

    def test_size_prunes_expired(self, monkeypatch: pytest.MonkeyPatch) -> None:
        cache = ResponseCache(max_size=4, default_ttl=60)
        current = {"t": 1000.0}
        monkeypatch.setattr("mrag.cache.response_cache.time.time", lambda: current["t"])
        cache.put("k1", _resp(), ttl=5)
        cache.put("k2", _resp(), ttl=500)
        current["t"] = 1010.0
        # k1 should be expired and pruned.
        assert cache.size == 1

    def test_invalid_args(self) -> None:
        with pytest.raises(ValueError):
            ResponseCache(max_size=0)
        with pytest.raises(ValueError):
            ResponseCache(max_size=2, default_ttl=0)
