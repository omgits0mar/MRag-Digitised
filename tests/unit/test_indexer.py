"""Unit tests for FAISS indexer in mrag.embeddings.indexer."""

import numpy as np
import pytest

from mrag.exceptions import RetrievalError


class TestFAISSIndexer:
    @pytest.fixture()
    def indexer(self) -> None:
        from mrag.embeddings.indexer import FAISSIndexer

        return FAISSIndexer(dimension=8)

    @pytest.fixture()
    def sample_vectors(self) -> np.ndarray:
        rng = np.random.RandomState(42)
        vecs = rng.randn(20, 8).astype(np.float32)
        vecs /= np.linalg.norm(vecs, axis=1, keepdims=True)
        return vecs

    def test_build_index(self) -> None:
        from mrag.embeddings.indexer import FAISSIndexer

        idx = FAISSIndexer(dimension=8)
        rng = np.random.RandomState(42)
        vecs = rng.randn(10, 8).astype(np.float32)
        vecs /= np.linalg.norm(vecs, axis=1, keepdims=True)
        idx.build_index(vecs)
        # Should not raise

    def test_search_returns_correct_shape(self) -> None:
        from mrag.embeddings.indexer import FAISSIndexer

        idx = FAISSIndexer(dimension=8)
        rng = np.random.RandomState(42)
        vecs = rng.randn(20, 8).astype(np.float32)
        vecs /= np.linalg.norm(vecs, axis=1, keepdims=True)
        idx.build_index(vecs)

        query = vecs[0:1]
        scores, indices = idx.search(query, top_k=5)
        assert scores.shape == (5,)
        assert indices.shape == (5,)

    def test_search_top1_is_nearest(self) -> None:
        from mrag.embeddings.indexer import FAISSIndexer

        idx = FAISSIndexer(dimension=8)
        rng = np.random.RandomState(42)
        vecs = rng.randn(20, 8).astype(np.float32)
        vecs /= np.linalg.norm(vecs, axis=1, keepdims=True)
        idx.build_index(vecs)

        query = vecs[3:4]
        scores, indices = idx.search(query, top_k=1)
        assert indices[0] == 3
        assert scores[0] > 0.99  # Self-similarity should be ~1.0

    def test_save_load_roundtrip(self, tmp_path: object) -> None:
        from mrag.embeddings.indexer import FAISSIndexer

        idx = FAISSIndexer(dimension=8)
        rng = np.random.RandomState(42)
        vecs = rng.randn(10, 8).astype(np.float32)
        vecs /= np.linalg.norm(vecs, axis=1, keepdims=True)
        idx.build_index(vecs)

        path = (
            str(tmp_path) + "/test.faiss"
            if isinstance(tmp_path, object)
            else f"{tmp_path}/test.faiss"
        )
        # Use a simple string path
        from pathlib import Path

        path = str(Path(str(tmp_path)) / "test.faiss")
        idx.save(path)

        idx2 = FAISSIndexer(dimension=8)
        idx2.load(path)

        query = vecs[0:1]
        scores1, indices1 = idx.search(query, top_k=3)
        scores2, indices2 = idx2.search(query, top_k=3)

        np.testing.assert_array_equal(indices1, indices2)
        np.testing.assert_allclose(scores1, scores2, atol=1e-6)

    def test_dimension_mismatch_raises(self) -> None:
        from mrag.embeddings.indexer import FAISSIndexer

        idx = FAISSIndexer(dimension=8)
        bad_vecs = np.random.randn(5, 16).astype(np.float32)
        with pytest.raises(RetrievalError):
            idx.build_index(bad_vecs)

    def test_load_nonexistent_raises(self) -> None:
        from mrag.embeddings.indexer import FAISSIndexer

        idx = FAISSIndexer(dimension=8)
        with pytest.raises(RetrievalError):
            idx.load("/nonexistent/path.faiss")

    def test_search_without_build_raises(self) -> None:
        from mrag.embeddings.indexer import FAISSIndexer

        idx = FAISSIndexer(dimension=8)
        query = np.random.randn(1, 8).astype(np.float32)
        with pytest.raises(RetrievalError):
            idx.search(query, top_k=5)
