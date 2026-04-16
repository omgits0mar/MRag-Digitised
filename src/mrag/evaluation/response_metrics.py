"""Response quality metrics — BLEU (sacrebleu) and ROUGE (rouge-score)."""

from __future__ import annotations

import sacrebleu
from rouge_score.rouge_scorer import RougeScorer


def compute_bleu(
    predictions: list[str],
    references: list[str],
) -> float:
    """Corpus-level BLEU score via sacrebleu.

    Args:
        predictions: Generated answer texts.
        references: Ground-truth reference answer texts.

    Returns:
        Float in [0, 1] (sacrebleu's 0-100 scale normalized).
    """
    if not predictions or not references:
        return 0.0
    result = sacrebleu.corpus_bleu(predictions, [references])
    return result.score / 100.0


def compute_rouge(
    predictions: list[str],
    references: list[str],
) -> dict[str, float]:
    """ROUGE-1, ROUGE-2, ROUGE-L fmeasure scores.

    Uses Google's rouge-score library with stemming enabled.

    Args:
        predictions: Generated answer texts.
        references: Ground-truth reference answer texts.

    Returns:
        {"rouge_1": float, "rouge_2": float, "rouge_l": float}
        Each in [0, 1], averaged over all pairs.
    """
    if not predictions or not references:
        return {"rouge_1": 0.0, "rouge_2": 0.0, "rouge_l": 0.0}

    scorer = RougeScorer(["rouge1", "rouge2", "rougeL"], use_stemmer=True)

    rouge_1_scores: list[float] = []
    rouge_2_scores: list[float] = []
    rouge_l_scores: list[float] = []

    for pred, ref in zip(predictions, references, strict=False):
        scores = scorer.score(ref, pred)
        rouge_1_scores.append(scores["rouge1"].fmeasure)
        rouge_2_scores.append(scores["rouge2"].fmeasure)
        rouge_l_scores.append(scores["rougeL"].fmeasure)

    return {
        "rouge_1": sum(rouge_1_scores) / len(rouge_1_scores),
        "rouge_2": sum(rouge_2_scores) / len(rouge_2_scores),
        "rouge_l": sum(rouge_l_scores) / len(rouge_l_scores),
    }
