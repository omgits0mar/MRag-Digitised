"""Unit tests for response quality metrics (BLEU and ROUGE)."""

from __future__ import annotations

import json

import pytest

from mrag.evaluation.response_metrics import compute_bleu, compute_rouge


class TestComputeBleu:
    def test_identical_text(self):
        score = compute_bleu(
            ["process by which plants convert light energy into chemical energy"],
            ["process by which plants convert light energy into chemical energy"],
        )
        assert score == pytest.approx(1.0, abs=0.01)

    def test_disjoint_text(self):
        score = compute_bleu(
            ["completely unrelated answer about cooking"],
            ["eight"],
        )
        assert score < 0.1

    def test_empty_inputs(self):
        assert compute_bleu([], []) == 0.0

    def test_partial_overlap(self):
        score = compute_bleu(
            ["William Shakespeare wrote Romeo and Juliet"],
            ["William Shakespeare"],
        )
        assert score > 0.1


class TestComputeRouge:
    def test_identical_text(self):
        scores = compute_rouge(["Paris"], ["Paris"])
        assert scores["rouge_l"] == pytest.approx(1.0, abs=0.01)
        assert scores["rouge_1"] == pytest.approx(1.0, abs=0.01)

    def test_disjoint_text(self):
        scores = compute_rouge(
            ["completely unrelated answer about cooking"],
            ["eight"],
        )
        assert scores["rouge_1"] < 0.2

    def test_empty_inputs(self):
        scores = compute_rouge([], [])
        assert scores["rouge_1"] == 0.0
        assert scores["rouge_l"] == 0.0

    def test_partial_overlap(self):
        scores = compute_rouge(
            ["evaporation condensation and precipitation cycle"],
            ["evaporation, condensation, and precipitation"],
        )
        assert scores["rouge_1"] > 0.4


class TestFixturePairs:
    """Validate against test fixtures with expected value ranges."""

    @pytest.fixture
    def pairs(self):
        with open("tests/fixtures/eval_reference_answers.json") as f:
            return json.load(f)["pairs"]

    def test_identical_pairs_high_scores(self, pairs):
        for pair in pairs:
            if "expected_bleu" in pair and pair["expected_bleu"] == 1.0:
                bleu = compute_bleu([pair["prediction"]], [pair["reference"]])
                # BLEU can be 0 for single-word texts (no n-grams beyond unigram)
                # so we only assert high BLEU for multi-word texts
                if len(pair["prediction"].split()) > 3:
                    assert (
                        bleu > 0.3
                    ), f"Expected BLEU high for: {pair['prediction'][:30]}, got {bleu}"

    def test_disjoint_pairs_low_scores(self, pairs):
        for pair in pairs:
            if "expected_bleu_lt" in pair:
                bleu = compute_bleu([pair["prediction"]], [pair["reference"]])
                assert (
                    bleu < pair["expected_bleu_lt"]
                ), f"BLEU too high for: {pair['prediction'][:30]}"
