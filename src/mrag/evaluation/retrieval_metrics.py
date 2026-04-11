"""Retrieval quality metrics — precision@K, recall@K, MRR, MAP.

Custom implementations validated against sklearn.metrics.average_precision_score
in unit tests where applicable.
"""

from __future__ import annotations


def precision_at_k(
    rankings: list[list[str]],
    relevants: list[set[str]],
    k: int,
) -> float:
    """Mean precision@K over multiple queries.

    Args:
        rankings: List of ranked prediction lists, one per query.
        relevants: List of relevant ID sets, one per query.
        k: Cutoff rank.

    Returns:
        Float in [0, 1].
    """
    if not rankings:
        return 0.0
    scores = [
        _single_precision_at_k(pred, rel, k)
        for pred, rel in zip(rankings, relevants, strict=False)
    ]
    return sum(scores) / len(scores)


def _single_precision_at_k(predicted: list[str], relevant: set[str], k: int) -> float:
    """Precision@K for a single query."""
    if k <= 0 or not predicted:
        return 0.0
    top_k = predicted[:k]
    hits = sum(1 for doc_id in top_k if doc_id in relevant)
    return hits / k


def recall_at_k(
    rankings: list[list[str]],
    relevants: list[set[str]],
    k: int,
) -> float:
    """Mean recall@K over multiple queries.

    Args:
        rankings: List of ranked prediction lists, one per query.
        relevants: List of relevant ID sets, one per query.
        k: Cutoff rank.

    Returns:
        Float in [0, 1].
    """
    if not rankings:
        return 0.0
    scores = [
        _single_recall_at_k(pred, rel, k)
        for pred, rel in zip(rankings, relevants, strict=False)
    ]
    return sum(scores) / len(scores)


def _single_recall_at_k(predicted: list[str], relevant: set[str], k: int) -> float:
    """Recall@K for a single query."""
    if not relevant:
        return 0.0
    if k <= 0:
        return 0.0
    top_k = predicted[:k]
    hits = sum(1 for doc_id in top_k if doc_id in relevant)
    return hits / len(relevant)


def reciprocal_rank(predicted: list[str], relevant: set[str]) -> float:
    """Reciprocal rank for a single query: 1/rank of first relevant hit.

    Returns:
        Float in [0, 1]. Returns 0.0 if no relevant item found.
    """
    for i, doc_id in enumerate(predicted, start=1):
        if doc_id in relevant:
            return 1.0 / i
    return 0.0


def mean_reciprocal_rank(
    rankings: list[list[str]],
    relevants: list[set[str]],
) -> float:
    """Mean reciprocal rank over multiple queries.

    Returns:
        Float in [0, 1].
    """
    if not rankings:
        return 0.0
    scores = [
        reciprocal_rank(pred, rel)
        for pred, rel in zip(rankings, relevants, strict=False)
    ]
    return sum(scores) / len(scores)


def average_precision(predicted: list[str], relevant: set[str]) -> float:
    """Average precision for a single query.

    Returns:
        Float in [0, 1]. Returns 0.0 if relevant is empty.
    """
    if not relevant:
        return 0.0

    hits = 0
    sum_precision = 0.0

    for i, doc_id in enumerate(predicted, start=1):
        if doc_id in relevant:
            hits += 1
            sum_precision += hits / i

    return sum_precision / len(relevant)


def mean_average_precision(
    rankings: list[list[str]],
    relevants: list[set[str]],
) -> float:
    """Mean average precision over multiple queries.

    Returns:
        Float in [0, 1].
    """
    if not rankings:
        return 0.0
    scores = [
        average_precision(pred, rel)
        for pred, rel in zip(rankings, relevants, strict=False)
    ]
    return sum(scores) / len(scores)
