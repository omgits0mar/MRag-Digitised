"""POST /evaluate route.

Triggers the full evaluation suite and returns metrics.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from mrag.api.dependencies import get_evaluator
from mrag.api.schemas import (
    ErrorEnvelope,
    EvaluateRequest,
    EvaluateResponse,
    RegressionFlag,
)
from mrag.evaluation.runner import EvaluationRunner

router = APIRouter(tags=["evaluate"])


@router.post(
    "/evaluate",
    response_model=EvaluateResponse,
    responses={422: {"model": ErrorEnvelope}, 500: {"model": ErrorEnvelope}},
    summary="Run the evaluation suite and return metrics",
)
async def run_evaluation(
    body: EvaluateRequest,
    evaluator: EvaluationRunner = Depends(get_evaluator),
) -> EvaluateResponse:
    """Trigger a full evaluation run."""
    report = await evaluator.run_full_evaluation(
        dataset_path=body.dataset_path,
        k_values=body.k_values,
        generate_report=body.generate_report,
        compare_baseline=body.compare_baseline,
    )

    # Build flat retrieval dict
    retrieval = {}
    for k, v in report.retrieval.precision_at_k.items():
        retrieval[f"precision_at_{k}"] = v
    for k, v in report.retrieval.recall_at_k.items():
        retrieval[f"recall_at_{k}"] = v
    retrieval["mrr"] = report.retrieval.mrr
    retrieval["map"] = report.retrieval.map

    regressions = []
    if report.baseline_comparison:
        for d in report.baseline_comparison.deltas:
            regressions.append(
                RegressionFlag(
                    metric=d.metric,
                    baseline_value=d.baseline_value,
                    current_value=d.current_value,
                    delta_pct=d.delta_pct,
                )
            )

    return EvaluateResponse(
        retrieval=retrieval,
        response_quality={
            "bleu": report.response_quality.bleu,
            "rouge_1": report.response_quality.rouge_1,
            "rouge_2": report.response_quality.rouge_2,
            "rouge_l": report.response_quality.rouge_l,
        },
        benchmark={
            "p50_ms": report.benchmark.p50_ms,
            "p95_ms": report.benchmark.p95_ms,
            "p99_ms": report.benchmark.p99_ms,
            "qps": report.benchmark.qps,
        },
        regressions=regressions,
        report_path=report.report_path,
        total_queries=report.retrieval.num_queries,
    )
