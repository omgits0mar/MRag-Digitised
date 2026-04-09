"""Retriever service composing encoder, indexer, metadata store, and ranking.

Provides the high-level retrieval API: embed query -> search index ->
fetch metadata -> re-rank -> filter -> return results.

Optionally accepts an ``EmbeddingCache`` to skip redundant encoding.
"""

from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING

import structlog

from mrag.embeddings.encoder import EmbeddingEncoder
from mrag.embeddings.indexer import FAISSIndexer
from mrag.embeddings.metadata_store import MetadataStore
from mrag.exceptions import RetrievalError
from mrag.retrieval.models import RetrievalRequest, RetrievalResult
from mrag.retrieval.ranking import rerank

if TYPE_CHECKING:
    from mrag.cache.embedding_cache import EmbeddingCache

logger = structlog.get_logger(__name__)


class RetrieverService:
    """High-level retrieval service composing embedding, search, and re-ranking.

    Args:
        encoder: EmbeddingEncoder for query embedding.
        indexer: FAISSIndexer for vector search.
        metadata_store: MetadataStore for result enrichment.
        embedding_cache: Optional cache to avoid redundant encoding.
    """

    def __init__(
        self,
        encoder: EmbeddingEncoder,
        indexer: FAISSIndexer,
        metadata_store: MetadataStore,
        embedding_cache: EmbeddingCache | None = None,
    ) -> None:
        self._encoder = encoder
        self._indexer = indexer
        self._metadata_store = metadata_store
        self._embedding_cache = embedding_cache

    def retrieve(self, request: RetrievalRequest) -> list[RetrievalResult]:
        """Execute a full retrieval pipeline.

        1. Embed the query text
        2. Search FAISS index for candidates (may over-fetch)
        3. Fetch metadata for each candidate
        4. Apply metadata filters if specified
        5. Re-rank results
        6. Apply score threshold filter
        7. Return up to top_k results

        Args:
            request: RetrievalRequest with query and parameters.

        Returns:
            List of RetrievalResult, sorted by relevance_score descending.

        Raises:
            RetrievalError: If index not loaded or encoding fails.
        """
        logger.info(
            "retrieval_start",
            query=request.query[:50],
            top_k=request.top_k,
        )

        # Step 1: Embed query (check cache first)
        query_hash = hashlib.md5(request.query.encode("utf-8")).hexdigest()
        query_vector = None
        if self._embedding_cache is not None:
            query_vector = self._embedding_cache.get(query_hash)
        if query_vector is None:
            try:
                query_vector = self._encoder.encode_single(request.query)
            except Exception as exc:
                raise RetrievalError(
                    f"Query encoding failed: {exc}",
                ) from exc
            if self._embedding_cache is not None:
                self._embedding_cache.put(query_hash, query_vector)

        # Step 2: Search index — over-fetch if threshold filtering needed
        fetch_k = request.top_k
        if request.score_threshold is not None or request.metadata_filters:
            fetch_k = min(request.top_k * 2, 50)

        try:
            scores, indices = self._indexer.search(query_vector, top_k=fetch_k)
        except Exception as exc:
            raise RetrievalError(
                f"Index search failed: {exc}",
            ) from exc

        # Step 3: Fetch metadata for candidates
        raw_results: list[dict] = []
        for score, idx in zip(scores, indices, strict=False):
            try:
                entry = self._metadata_store.get(int(idx))
                raw_results.append(
                    {
                        "faiss_id": int(idx),
                        "chunk_id": entry.chunk_id,
                        "doc_id": entry.doc_id,
                        "chunk_text": entry.chunk_text,
                        "question": entry.question,
                        "answer_short": entry.answer_short,
                        "answer_long": entry.answer_long,
                        "question_type": entry.question_type,
                        "domain": entry.domain,
                        "difficulty": entry.difficulty,
                        "has_short_answer": entry.has_short_answer,
                        "cosine_similarity": float(score),
                    }
                )
            except KeyError:
                continue

        # Step 4: Apply metadata filters
        if request.metadata_filters:
            filtered: list[dict] = []
            for r in raw_results:
                match = all(
                    str(r.get(k)) == str(v) for k, v in request.metadata_filters.items()
                )
                if match:
                    filtered.append(r)
            raw_results = filtered

        # Step 5: Re-rank
        ranked = rerank(raw_results, request.query)

        # Step 6: Apply score threshold
        if request.score_threshold is not None:
            ranked = [r for r in ranked if r.relevance_score >= request.score_threshold]

        # Step 7: Cap at top_k
        ranked = ranked[: request.top_k]

        logger.info(
            "retrieval_complete",
            query=request.query[:50],
            results=len(ranked),
        )

        return ranked
