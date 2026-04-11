"""Unit tests for retrieval metrics with known-answer test cases."""

from __future__ import annotations

import pytest

from mrag.evaluation.retrieval_metrics import (
    average_precision,
    mean_average_precision,
    mean_reciprocal_rank,
    precision_at_k,
    recall_at_k,
    reciprocal_rank,
)


class TestPrecisionAtK:
    def test_perfect_retrieval(self):
        rankings = [["a", "b", "c"]]
        relevants = [{"a", "b", "c"}]
        assert precision_at_k(rankings, relevants, 3) == 1.0

    def test_empty_predictions(self):
        rankings = [[]]
        relevants = [{"a"}]
        assert precision_at_k(rankings, relevants, 3) == 0.0

    def test_half_relevant(self):
        rankings = [["a", "x", "b"]]
        relevants = [{"a", "b"}]
        assert precision_at_k(rankings, relevants, 2) == 0.5

    def test_multiple_queries(self):
        rankings = [["a", "b"], ["x", "y"]]
        relevants = [{"a", "b"}, {"x", "z"}]
        # Query 1: precision@2 = 2/2 = 1.0
        # Query 2: precision@2 = 1/2 = 0.5
        assert precision_at_k(rankings, relevants, 2) == 0.75


class TestRecallAtK:
    def test_perfect_recall(self):
        rankings = [["a", "b", "c"]]
        relevants = [{"a", "b"}]
        assert recall_at_k(rankings, relevants, 3) == 1.0

    def test_empty_relevant(self):
        rankings = [["a"]]
        relevants = [set()]
        assert recall_at_k(rankings, relevants, 1) == 0.0

    def test_partial_recall(self):
        rankings = [["a"]]
        relevants = [{"a", "b", "c"}]
        assert recall_at_k(rankings, relevants, 1) == pytest.approx(1 / 3)


class TestReciprocalRank:
    def test_first_position(self):
        assert reciprocal_rank(["a", "b"], {"a"}) == 1.0

    def test_second_position(self):
        assert reciprocal_rank(["x", "a"], {"a"}) == 0.5

    def test_no_match(self):
        assert reciprocal_rank(["x", "y"], {"a"}) == 0.0


class TestMeanReciprocalRank:
    def test_mrr(self):
        rankings = [["a", "b"], ["x", "a"]]
        relevants = [{"a"}, {"a"}]
        assert mean_reciprocal_rank(rankings, relevants) == 0.75


class TestAveragePrecision:
    def test_perfect_ranking(self):
        assert average_precision(["a", "b", "c"], {"a", "b", "c"}) == 1.0

    def test_empty_relevant(self):
        assert average_precision(["a"], set()) == 0.0

    def test_known_case(self):
        # ranked: [a, b, x, c], relevant: {a, b, c}
        # AP = (1/1 + 2/2 + 0 + 3/4) / 3 = (1 + 1 + 0.75) / 3 = 0.9167
        result = average_precision(["a", "b", "x", "c"], {"a", "b", "c"})
        assert result == pytest.approx(0.9167, abs=0.001)


class TestMeanAveragePrecision:
    def test_perfect(self):
        rankings = [["a", "b"], ["x", "y"]]
        relevants = [{"a", "b"}, {"x", "y"}]
        assert mean_average_precision(rankings, relevants) == 1.0

    def test_empty(self):
        assert mean_average_precision([], []) == 0.0

    def test_mixed(self):
        rankings = [["a", "b"], ["x", "y"]]
        relevants = [{"a"}, {"z"}]
        # AP1 = 1/1 / 1 = 1.0, AP2 = 0 / 1 = 0.0
        assert mean_average_precision(rankings, relevants) == 0.5
