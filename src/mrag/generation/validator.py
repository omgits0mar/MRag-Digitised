"""Response-quality validator with TF-IDF based context overlap scoring.

Confidence is a weighted combination of the average retrieval score
(signal: is the context itself relevant?) and the TF-IDF cosine overlap
between the generated answer and the retrieved context (signal: is the
answer actually grounded in that context?).
"""

from __future__ import annotations

import structlog
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from mrag.generation.models import ValidationResult
from mrag.retrieval.models import RetrievalResult

logger = structlog.get_logger(__name__)


class ResponseValidator:
    """Compute a confidence score for a generated answer.

    Args:
        confidence_threshold: Minimum confidence to be considered grounded.
        alpha: Weight applied to the retrieval signal; ``1 - alpha`` is
            applied to the TF-IDF overlap signal.
    """

    def __init__(
        self,
        confidence_threshold: float = 0.3,
        alpha: float = 0.6,
    ) -> None:
        if not 0.0 <= confidence_threshold <= 1.0:
            raise ValueError("confidence_threshold must be in [0.0, 1.0]")
        if not 0.0 <= alpha <= 1.0:
            raise ValueError("alpha must be in [0.0, 1.0]")
        self._threshold = confidence_threshold
        self._alpha = alpha

    def validate(
        self,
        response_text: str,
        context_chunks: list[RetrievalResult],
        retrieval_scores: list[float],
    ) -> ValidationResult:
        """Score ``response_text`` against its retrieved context.

        Returns a ``ValidationResult`` with the weighted confidence score
        and its components.
        """
        retrieval_avg = (
            float(sum(retrieval_scores) / len(retrieval_scores))
            if retrieval_scores
            else 0.0
        )
        retrieval_avg = max(0.0, min(1.0, retrieval_avg))

        overlap = self._compute_tfidf_overlap(response_text, context_chunks)
        confidence = self._alpha * retrieval_avg + (1.0 - self._alpha) * overlap
        confidence = max(0.0, min(1.0, confidence))

        result = ValidationResult(
            confidence_score=confidence,
            retrieval_score_avg=retrieval_avg,
            context_overlap=overlap,
            is_confident=confidence >= self._threshold,
            threshold_used=self._threshold,
        )
        logger.info(
            "response_validated",
            confidence=round(confidence, 3),
            retrieval_avg=round(retrieval_avg, 3),
            overlap=round(overlap, 3),
            is_confident=result.is_confident,
        )
        return result

    # ---------------------------------------------------------------- internals

    def _compute_tfidf_overlap(
        self,
        response_text: str,
        context_chunks: list[RetrievalResult],
    ) -> float:
        """TF-IDF cosine similarity between the answer and the joined context."""
        if not response_text or not response_text.strip():
            return 0.0
        if not context_chunks:
            return 0.0

        context_text = " ".join(c.chunk_text for c in context_chunks if c.chunk_text)
        if not context_text.strip():
            return 0.0

        try:
            vectorizer = TfidfVectorizer(lowercase=True, ngram_range=(1, 2))
            matrix = vectorizer.fit_transform([response_text, context_text])
            if matrix.shape[0] < 2:
                return 0.0
            sim = cosine_similarity(matrix[0:1], matrix[1:2])[0, 0]
        except ValueError:
            # Empty vocabulary after stopword removal, etc.
            return 0.0

        return float(max(0.0, min(1.0, sim)))
