"""Unit tests for mrag.generation.validator.ResponseValidator."""

from __future__ import annotations

from mrag.generation.validator import ResponseValidator
from mrag.retrieval.models import RetrievalResult


def _chunk(text: str, score: float = 0.8) -> RetrievalResult:
    return RetrievalResult(
        chunk_id="c",
        doc_id="d",
        chunk_text=text,
        relevance_score=score,
        cosine_similarity=score,
        question="q",
        answer_short=None,
        answer_long=text,
        question_type="factoid",
        domain="science",
        difficulty="easy",
        has_short_answer=False,
    )


class TestResponseValidator:
    def test_high_signals_produce_high_confidence(self) -> None:
        val = ResponseValidator(confidence_threshold=0.3, alpha=0.6)
        chunks = [
            _chunk(
                "Photosynthesis is the process by which plants convert light "
                "energy into chemical energy using chlorophyll.",
                0.95,
            ),
        ]
        answer = (
            "Photosynthesis is the process plants use to convert light "
            "energy into chemical energy via chlorophyll."
        )
        result = val.validate(answer, chunks, [0.95])
        assert result.confidence_score > 0.5
        assert result.is_confident is True

    def test_low_signals_low_confidence(self) -> None:
        val = ResponseValidator(confidence_threshold=0.3, alpha=0.6)
        chunks = [_chunk("unrelated alpaca farming instructions", 0.05)]
        answer = "Quantum computing uses qubits in superposition."
        result = val.validate(answer, chunks, [0.05])
        assert result.confidence_score < 0.3
        assert result.is_confident is False

    def test_empty_context_near_zero(self) -> None:
        val = ResponseValidator(confidence_threshold=0.3)
        result = val.validate("some answer", [], [])
        assert result.confidence_score == 0.0
        assert result.retrieval_score_avg == 0.0
        assert result.context_overlap == 0.0
        assert result.is_confident is False

    def test_threshold_boundary_is_inclusive(self) -> None:
        val = ResponseValidator(confidence_threshold=0.5, alpha=1.0)
        chunks = [_chunk("context text", 0.5)]
        result = val.validate("unused", chunks, [0.5])
        # alpha=1.0 means confidence == retrieval_avg == 0.5 exactly.
        assert result.confidence_score == 0.5
        assert result.is_confident is True

    def test_empty_response_text_zero_overlap(self) -> None:
        val = ResponseValidator(confidence_threshold=0.3)
        chunks = [_chunk("some context")]
        result = val.validate("", chunks, [0.8])
        assert result.context_overlap == 0.0

    def test_invalid_alpha_raises(self) -> None:
        import pytest

        with pytest.raises(ValueError):
            ResponseValidator(alpha=1.5)

    def test_invalid_threshold_raises(self) -> None:
        import pytest

        with pytest.raises(ValueError):
            ResponseValidator(confidence_threshold=-0.1)
