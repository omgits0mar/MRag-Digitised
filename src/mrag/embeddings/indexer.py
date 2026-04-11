"""FAISS vector index wrapper for MRAG.

Builds and searches a FAISS IndexFlatIP from L2-normalized embeddings,
with persistence to disk and dimension validation.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import structlog

from mrag.exceptions import RetrievalError

logger = structlog.get_logger(__name__)


class FAISSIndexer:
    """FAISS index wrapper for vector storage and similarity search.

    Uses IndexFlatIP (inner product) on L2-normalized vectors, which
    is equivalent to cosine similarity.

    Args:
        dimension: Vector dimensionality (must match embedding model output).
        index_type: FAISS index type string (currently only "Flat" supported).
    """

    def __init__(self, dimension: int = 384, index_type: str = "Flat") -> None:
        self._dimension = dimension
        self._index_type = index_type
        self._index = None

    @property
    def is_loaded(self) -> bool:
        """Whether the FAISS index has been loaded into memory."""
        return self._index is not None

    def build_index(self, vectors: np.ndarray) -> None:
        """Build the FAISS index from a matrix of L2-normalized vectors.

        Args:
            vectors: np.ndarray of shape (n, dimension), L2-normalized.

        Raises:
            RetrievalError: If dimension mismatch or build fails.
        """
        import faiss

        if vectors.ndim != 2 or vectors.shape[1] != self._dimension:
            raise RetrievalError(
                f"Dimension mismatch: expected (n, {self._dimension}), "
                f"got {vectors.shape}",
                detail={
                    "expected_dim": self._dimension,
                    "got_shape": list(vectors.shape),
                },
            )

        try:
            self._index = faiss.IndexFlatIP(self._dimension)
            self._index.add(vectors.astype(np.float32))
            logger.info(
                "index_built",
                num_vectors=vectors.shape[0],
                dimension=self._dimension,
            )
        except Exception as exc:
            raise RetrievalError(
                f"Failed to build index: {exc}",
            ) from exc

    def search(
        self, query_vector: np.ndarray, top_k: int = 5
    ) -> tuple[np.ndarray, np.ndarray]:
        """Search for nearest neighbors.

        Args:
            query_vector: Shape (dimension,) or (1, dimension), L2-normalized.
            top_k: Number of results.

        Returns:
            Tuple of (scores, indices) each of shape (top_k,).

        Raises:
            RetrievalError: If index not loaded or search fails.
        """
        if self._index is None:
            raise RetrievalError("Index not built or loaded")

        if query_vector.ndim == 1:
            query_vector = query_vector.reshape(1, -1)

        query_vector = query_vector.astype(np.float32)

        scores, indices = self._index.search(query_vector, top_k)
        return scores[0], indices[0]

    def save(self, path: str) -> None:
        """Persist index to disk."""
        import faiss

        if self._index is None:
            raise RetrievalError("No index to save")

        Path(path).parent.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self._index, path)
        logger.info("index_saved", path=path)

    def load(self, path: str) -> None:
        """Load index from disk.

        Args:
            path: Path to .faiss file.

        Raises:
            RetrievalError: If file not found or corrupted.
        """
        import faiss

        if not Path(path).exists():
            raise RetrievalError(
                f"Index file not found: {path}",
                detail={"path": path},
            )

        try:
            self._index = faiss.read_index(path)
            logger.info("index_loaded", path=path, num_vectors=self._index.ntotal)
        except Exception as exc:
            raise RetrievalError(
                f"Failed to load index: {exc}",
            ) from exc

    @property
    def ntotal(self) -> int:
        """Number of vectors in the index."""
        if self._index is None:
            return 0
        return self._index.ntotal
