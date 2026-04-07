"""Re-ranking module for retrieval results.

Implements weighted scoring combining cosine similarity with metadata
relevance signals for improved retrieval quality.
"""

from __future__ import annotations

import re

from mrag.retrieval.models import RetrievalResult

# Patterns for query-aware metadata boosting
_FACTOID_QUERY_RE = re.compile(
    r"^(who|what|when|where|which|how many|how much)\b", re.IGNORECASE
)
_YES_NO_QUERY_RE = re.compile(
    r"^(is|are|was|were|do|does|did|can|could)\b", re.IGNORECASE
)
_LIST_QUERY_RE = re.compile(r"^(list|name)\b", re.IGNORECASE)
_DESCRIPTIVE_QUERY_RE = re.compile(
    r"^(explain|describe|why|how (does|do|is|are))\b", re.IGNORECASE
)


def _query_type_hint(query: str) -> str | None:
    """Guess question type from query text for metadata boost."""
    if _DESCRIPTIVE_QUERY_RE.match(query):
        return "descriptive"
    if _LIST_QUERY_RE.match(query):
        return "list"
    if _YES_NO_QUERY_RE.match(query):
        return "yes_no"
    if _FACTOID_QUERY_RE.match(query):
        return "factoid"
    return None


def rerank(
    results: list[dict],
    query: str,
    alpha: float = 0.7,
) -> list[RetrievalResult]:
    """Re-rank search results using weighted scoring.

    Scoring formula:
        relevance_score = alpha * cosine_similarity + (1 - alpha) * metadata_boost

    Metadata boost considers:
    - +0.1 if has_short_answer (answer availability signal)
    - +0.1 if question_type matches query pattern
    - Boost capped at 1.0

    Args:
        results: Raw search results with cosine_similarity and metadata.
        query: Original query text.
        alpha: Weight for cosine similarity vs metadata boost (default 0.7).

    Returns:
        List of RetrievalResult sorted by relevance_score descending.
    """
    if not results:
        return []

    query_type_hint = _query_type_hint(query)
    ranked: list[RetrievalResult] = []

    for result in results:
        cosine_sim = result["cosine_similarity"]

        # Compute metadata boost
        metadata_boost = 0.0

        # Answer availability signal
        if result.get("has_short_answer"):
            metadata_boost += 0.1

        # Question type match
        if query_type_hint and result.get("question_type") == query_type_hint:
            metadata_boost += 0.1

        # Cap boost
        metadata_boost = min(metadata_boost, 1.0)

        # Weighted combination
        relevance_score = alpha * cosine_sim + (1 - alpha) * metadata_boost
        relevance_score = max(0.0, min(1.0, relevance_score))

        ranked.append(
            RetrievalResult(
                chunk_id=result["chunk_id"],
                doc_id=result["doc_id"],
                chunk_text=result["chunk_text"],
                relevance_score=relevance_score,
                cosine_similarity=cosine_sim,
                question=result["question"],
                answer_short=result.get("answer_short"),
                answer_long=result["answer_long"],
                question_type=result["question_type"],
                domain=result["domain"],
                difficulty=result["difficulty"],
                has_short_answer=result["has_short_answer"],
            )
        )

    ranked.sort(key=lambda r: r.relevance_score, reverse=True)
    return ranked
