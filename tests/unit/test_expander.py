"""Unit tests for mrag.query.expander.QueryExpander."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from mrag.exceptions import QueryProcessingError
from mrag.query.expander import QueryExpander
from mrag.retrieval.models import RetrievalResult


def _mk_result(
    chunk_id: str,
    doc_id: str,
    text: str,
    score: float = 0.8,
) -> RetrievalResult:
    return RetrievalResult(
        chunk_id=chunk_id,
        doc_id=doc_id,
        chunk_text=text,
        relevance_score=score,
        cosine_similarity=score,
        question="q",
        answer_short="a",
        answer_long=text,
        question_type="factoid",
        domain="science",
        difficulty="easy",
        has_short_answer=True,
    )


class TestQueryExpander:
    def test_short_query_produces_expansion_terms(self) -> None:
        retriever = MagicMock()
        retriever.retrieve.return_value = [
            _mk_result(
                "c1",
                "d1",
                "deoxyribonucleic acid carries genetic instructions chromosome",
                0.9,
            ),
            _mk_result(
                "c2",
                "d2",
                "nucleic acid chromosome genetic material molecule biology",
                0.8,
            ),
            _mk_result(
                "c3",
                "d3",
                "chromosome carries genetic sequence nucleotides helix",
                0.7,
            ),
        ]
        expander = QueryExpander(retriever=retriever)
        result = expander.expand("dna")
        assert result.original_query == "dna"
        assert result.expanded_query != "dna"
        assert len(result.expansion_terms) > 0
        assert len(result.expansion_terms) <= 5
        # Expanded query preserves the original query terms.
        assert "dna" in result.expanded_query

    def test_expansion_preserves_original_terms(self) -> None:
        retriever = MagicMock()
        retriever.retrieve.return_value = [
            _mk_result("c1", "d1", "photosynthesis chlorophyll plant light", 0.9),
        ]
        expander = QueryExpander(retriever=retriever)
        result = expander.expand("plants and light")
        assert "plants" in result.expanded_query
        assert "light" in result.expanded_query

    def test_empty_retrieval_returns_original(self) -> None:
        retriever = MagicMock()
        retriever.retrieve.return_value = []
        expander = QueryExpander(retriever=retriever)
        result = expander.expand("rare query")
        assert result.expanded_query == "rare query"
        assert result.expansion_terms == []

    def test_retriever_exception_is_safe(self) -> None:
        retriever = MagicMock()
        retriever.retrieve.side_effect = RuntimeError("index missing")
        expander = QueryExpander(retriever=retriever)
        result = expander.expand("test")
        assert result.expanded_query == "test"
        assert result.expansion_terms == []

    def test_zero_top_n_disables_expansion(self) -> None:
        retriever = MagicMock()
        expander = QueryExpander(retriever=retriever)
        result = expander.expand("test", top_n=0)
        assert result.expanded_query == "test"
        retriever.retrieve.assert_not_called()

    def test_empty_query_raises(self) -> None:
        expander = QueryExpander(retriever=MagicMock())
        with pytest.raises(QueryProcessingError):
            expander.expand("   ")

    def test_prf_doc_ids_populated(self) -> None:
        retriever = MagicMock()
        retriever.retrieve.return_value = [
            _mk_result("c1", "doc_a", "foo bar baz", 0.9),
            _mk_result("c2", "doc_b", "alpha beta gamma", 0.8),
        ]
        expander = QueryExpander(retriever=retriever)
        result = expander.expand("query")
        assert result.prf_doc_ids == ["doc_a", "doc_b"]
