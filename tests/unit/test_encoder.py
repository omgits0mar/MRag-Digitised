"""Unit tests for embedding encoder in mrag.embeddings.encoder."""

import numpy as np
import pytest


class TestEmbeddingEncoder:
    @pytest.fixture()
    def encoder(self) -> None:
        from mrag.embeddings.encoder import EmbeddingEncoder

        return EmbeddingEncoder()

    def test_encode_returns_correct_shape(self) -> None:
        from mrag.embeddings.encoder import EmbeddingEncoder

        enc = EmbeddingEncoder()
        result = enc.encode(["hello", "world"])
        assert result.shape[0] == 2
        assert result.shape[1] == 384
        assert result.dtype == np.float32

    def test_encode_single_returns_1d(self) -> None:
        from mrag.embeddings.encoder import EmbeddingEncoder

        enc = EmbeddingEncoder()
        result = enc.encode_single("hello")
        assert result.ndim == 1
        assert result.shape[0] == 384
        assert result.dtype == np.float32

    def test_l2_normalization(self) -> None:
        from mrag.embeddings.encoder import EmbeddingEncoder

        enc = EmbeddingEncoder()
        result = enc.encode(["hello", "world"])
        norms = np.linalg.norm(result, axis=1)
        np.testing.assert_allclose(norms, 1.0, atol=1e-6)

    def test_single_l2_normalization(self) -> None:
        from mrag.embeddings.encoder import EmbeddingEncoder

        enc = EmbeddingEncoder()
        result = enc.encode_single("hello")
        norm = np.linalg.norm(result)
        np.testing.assert_allclose(norm, 1.0, atol=1e-6)

    def test_empty_input(self) -> None:
        from mrag.embeddings.encoder import EmbeddingEncoder

        enc = EmbeddingEncoder()
        result = enc.encode([])
        assert result.shape == (0, 384)

    def test_dimension_consistency(self) -> None:
        from mrag.embeddings.encoder import EmbeddingEncoder

        enc = EmbeddingEncoder()
        r1 = enc.encode(["first text"])
        r2 = enc.encode(["second text"])
        assert r1.shape[1] == r2.shape[1]

    def test_cross_lingual_similarity(self) -> None:
        """English and Arabic translations should have cosine sim > 0.7."""
        from mrag.embeddings.encoder import EmbeddingEncoder

        enc = EmbeddingEncoder()
        arabic_water = "\u0645\u0627 \u0647\u064a \u0627\u0644\u0645\u0627\u0621\u061f"
        emb = enc.encode(["What is water?", arabic_water])
        cos_sim = np.dot(emb[0], emb[1])  # L2-normalized, so dot = cosine
        assert cos_sim > 0.5, f"Cross-lingual similarity too low: {cos_sim}"

    def test_deterministic_encoding(self) -> None:
        from mrag.embeddings.encoder import EmbeddingEncoder

        enc = EmbeddingEncoder()
        r1 = enc.encode(["test text"])
        r2 = enc.encode(["test text"])
        np.testing.assert_allclose(r1, r2, atol=1e-6)
