"""Unit tests for mrag.query.preprocessor.QueryPreprocessor."""

from __future__ import annotations

import pytest

from mrag.exceptions import QueryProcessingError
from mrag.query.preprocessor import QueryPreprocessor


class TestQueryPreprocessorNormalize:
    def test_collapses_extra_whitespace(self) -> None:
        pre = QueryPreprocessor()
        assert (
            pre.normalize("  What  IS   Photosynthesis?? ") == "what is photosynthesis"
        )

    def test_lowercases_mixed_casing(self) -> None:
        pre = QueryPreprocessor()
        assert pre.normalize("WHO is Albert EINSTEIN") == "who is albert einstein"

    def test_preserves_arabic(self) -> None:
        pre = QueryPreprocessor()
        arabic = "ما هو التعلم الآلي؟"
        result = pre.normalize(arabic)
        # Should still contain meaningful Arabic content and strip trailing '?'.
        assert "؟" not in result or not result.endswith("؟")
        assert len(result) > 0

    def test_preserves_french_accents(self) -> None:
        pre = QueryPreprocessor()
        result = pre.normalize("Qu'est-ce que l'Énergie ?")
        assert "énergie" in result
        assert not result.endswith("?")

    def test_preserves_chinese(self) -> None:
        pre = QueryPreprocessor()
        result = pre.normalize("什么是机器学习？")
        assert "什么是机器学习" in result

    def test_strips_trailing_excessive_punctuation(self) -> None:
        pre = QueryPreprocessor()
        assert pre.normalize("What is DNA???!!!") == "what is dna"

    def test_nfc_normalizes_combining_marks(self) -> None:
        pre = QueryPreprocessor()
        decomposed = "cafe\u0301"  # "café" via combining acute
        composed = pre.normalize(decomposed)
        # NFC composes the combining acute into a single 'é' codepoint.
        assert composed == "café"

    def test_empty_string_raises(self) -> None:
        pre = QueryPreprocessor()
        with pytest.raises(QueryProcessingError):
            pre.normalize("")

    def test_whitespace_only_raises(self) -> None:
        pre = QueryPreprocessor()
        with pytest.raises(QueryProcessingError):
            pre.normalize("   \n\t  ")

    def test_punctuation_only_raises(self) -> None:
        pre = QueryPreprocessor()
        with pytest.raises(QueryProcessingError):
            pre.normalize("????!!!")

    def test_none_raises(self) -> None:
        pre = QueryPreprocessor()
        with pytest.raises(QueryProcessingError):
            pre.normalize(None)  # type: ignore[arg-type]
