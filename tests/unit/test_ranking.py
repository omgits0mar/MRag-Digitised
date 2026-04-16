"""Unit tests for re-ranking in mrag.retrieval.ranking."""

from mrag.data.models import QuestionType


class TestRerank:
    def test_results_sorted_by_relevance_score(self) -> None:
        from mrag.retrieval.ranking import rerank

        results = [
            _make_raw_result(0, 0.5, "science", True, QuestionType.FACTOID),
            _make_raw_result(1, 0.9, "history", False, QuestionType.DESCRIPTIVE),
            _make_raw_result(2, 0.7, "science", True, QuestionType.FACTOID),
        ]
        ranked = rerank(results, "What is science?")
        scores = [r.relevance_score for r in ranked]
        assert scores == sorted(scores, reverse=True)

    def test_relevance_score_bounds(self) -> None:
        from mrag.retrieval.ranking import rerank

        results = [
            _make_raw_result(0, 1.0, "science", True, QuestionType.FACTOID),
            _make_raw_result(1, 0.0, "history", False, QuestionType.UNKNOWN),
        ]
        ranked = rerank(results, "What is X?")
        for r in ranked:
            assert 0.0 <= r.relevance_score <= 1.0

    def test_deterministic_output(self) -> None:
        from mrag.retrieval.ranking import rerank

        results = [
            _make_raw_result(0, 0.8, "science", True, QuestionType.FACTOID),
            _make_raw_result(1, 0.6, "history", False, QuestionType.DESCRIPTIVE),
        ]
        ranked1 = rerank(results, "What is science?")
        ranked2 = rerank(results, "What is science?")
        for r1, r2 in zip(ranked1, ranked2, strict=False):
            assert r1.relevance_score == r2.relevance_score

    def test_higher_cosine_gives_higher_score(self) -> None:
        from mrag.retrieval.ranking import rerank

        results = [
            _make_raw_result(0, 0.3, "science", False, QuestionType.UNKNOWN),
            _make_raw_result(1, 0.9, "science", False, QuestionType.UNKNOWN),
        ]
        ranked = rerank(results, "What is science?")
        assert ranked[0].cosine_similarity == 0.9
        assert ranked[0].relevance_score > ranked[1].relevance_score

    def test_metadata_boost_with_short_answer(self) -> None:
        from mrag.retrieval.ranking import rerank

        # Same cosine sim, but one has short answer
        results = [
            _make_raw_result(0, 0.8, "science", False, QuestionType.FACTOID),
            _make_raw_result(1, 0.8, "science", True, QuestionType.FACTOID),
        ]
        ranked = rerank(results, "Who is Einstein?")
        # Result with short answer should rank higher
        assert ranked[0].chunk_text == "chunk 1"


class TestRerankEdgeCases:
    def test_empty_results(self) -> None:
        from mrag.retrieval.ranking import rerank

        ranked = rerank([], "query")
        assert ranked == []

    def test_single_result(self) -> None:
        from mrag.retrieval.ranking import rerank

        results = [_make_raw_result(0, 0.8, "science", True, QuestionType.FACTOID)]
        ranked = rerank(results, "What is science?")
        assert len(ranked) == 1
        assert ranked[0].relevance_score > 0.0


def _make_raw_result(
    faiss_id: int,
    cosine_sim: float,
    domain: str,
    has_short: bool,
    question_type: QuestionType,
) -> dict:
    return {
        "faiss_id": faiss_id,
        "chunk_id": f"chunk_{faiss_id}",
        "doc_id": f"doc_{faiss_id}",
        "chunk_text": f"chunk {faiss_id}",
        "question": "What is X?",
        "answer_short": "Answer" if has_short else None,
        "answer_long": "Long answer text.",
        "question_type": question_type,
        "domain": domain,
        "difficulty": "easy",
        "has_short_answer": has_short,
        "cosine_similarity": cosine_sim,
    }
