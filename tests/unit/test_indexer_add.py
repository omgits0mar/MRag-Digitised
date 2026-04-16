"""Tests for FAISSIndexer.add_vectors incremental-add support."""

from __future__ import annotations

import numpy as np
import pytest

from mrag.embeddings.indexer import FAISSIndexer
from mrag.exceptions import RetrievalError


def _rand_normalized(n: int, dim: int, seed: int) -> np.ndarray:
    rng = np.random.RandomState(seed)
    vecs = rng.randn(n, dim).astype(np.float32)
    vecs /= np.linalg.norm(vecs, axis=1, keepdims=True)
    return vecs


class TestAddVectors:
    def test_add_vectors_initializes_empty_index(self) -> None:
        idx = FAISSIndexer(dimension=8)
        assert idx.ntotal == 0
        ids = idx.add_vectors(_rand_normalized(3, 8, seed=1))
        assert ids == [0, 1, 2]
        assert idx.ntotal == 3

    def test_add_vectors_appends_to_existing_index(self) -> None:
        idx = FAISSIndexer(dimension=8)
        idx.build_index(_rand_normalized(5, 8, seed=2))
        ids = idx.add_vectors(_rand_normalized(4, 8, seed=3))
        assert ids == [5, 6, 7, 8]
        assert idx.ntotal == 9

    def test_search_finds_newly_added_vector(self) -> None:
        idx = FAISSIndexer(dimension=8)
        initial = _rand_normalized(5, 8, seed=4)
        idx.build_index(initial)

        extra = _rand_normalized(1, 8, seed=99)
        new_ids = idx.add_vectors(extra)

        scores, indices = idx.search(extra[0], top_k=1)
        assert indices[0] == new_ids[0]
        assert scores[0] > 0.99

    def test_add_vectors_dimension_mismatch_raises(self) -> None:
        idx = FAISSIndexer(dimension=8)
        with pytest.raises(RetrievalError):
            idx.add_vectors(np.random.randn(2, 16).astype(np.float32))
