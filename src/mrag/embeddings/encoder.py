"""Embedding encoder wrapping Sentence Transformers for MRAG.

Generates L2-normalized multilingual embeddings using sentence-transformers
with batch processing and lazy model loading.
"""

from __future__ import annotations

import numpy as np
import structlog
from sklearn.preprocessing import normalize

from mrag.exceptions import EmbeddingError

logger = structlog.get_logger(__name__)


class EmbeddingEncoder:
    """Wrapper around Sentence Transformers for multilingual embedding generation.

    Args:
        model_name: Name of the sentence-transformers model to use.
    """

    def __init__(
        self, model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"
    ) -> None:
        self._model_name = model_name
        self._model = None

    def _load_model(self) -> None:
        """Lazy-load the sentence transformer model."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer

                logger.info("loading_embedding_model", model=self._model_name)
                self._model = SentenceTransformer(self._model_name)
                logger.info("embedding_model_loaded")
            except Exception as exc:
                raise EmbeddingError(
                    f"Failed to load embedding model: {exc}",
                    detail={"model": self._model_name},
                ) from exc

    def encode(self, texts: list[str], batch_size: int = 64) -> np.ndarray:
        """Generate L2-normalized embeddings for a batch of texts.

        Args:
            texts: List of text strings to embed.
            batch_size: Processing batch size.

        Returns:
            np.ndarray of shape (len(texts), embedding_dim), float32, L2-normalized.

        Raises:
            EmbeddingError: If encoding fails.
        """
        if not texts:
            self._load_model()
            dim = self._model.get_sentence_embedding_dimension()
            return np.zeros((0, dim), dtype=np.float32)

        self._load_model()

        try:
            logger.info("encoding_start", count=len(texts), batch_size=batch_size)
            embeddings = self._model.encode(
                texts,
                batch_size=batch_size,
                show_progress_bar=False,
                convert_to_numpy=True,
            )
            embeddings = np.asarray(embeddings, dtype=np.float32)

            # L2 normalize
            embeddings = normalize(embeddings, norm="l2", axis=1)

            logger.info("encoding_complete", shape=embeddings.shape)
            return embeddings
        except Exception as exc:
            raise EmbeddingError(
                f"Encoding failed: {exc}",
                detail={"count": len(texts)},
            ) from exc

    def encode_single(self, text: str) -> np.ndarray:
        """Generate embedding for a single text.

        Args:
            text: Text string to embed.

        Returns:
            np.ndarray of shape (embedding_dim,), float32, L2-normalized.
        """
        result = self.encode([text])
        return result[0]
