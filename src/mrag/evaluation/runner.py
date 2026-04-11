"""Evaluation runner orchestrating the full evaluation suite.

Can be invoked from the API endpoint (POST /evaluate) or standalone (FR-022).
"""

from __future__ import annotations

import structlog

from mrag.evaluation.models import EvaluationReport

logger = structlog.get_logger(__name__)


class EvaluationRunner:
    """Orchestrates the full evaluation suite.

    Args:
        pipeline: MRAGPipeline instance for running queries.
        settings: Optional Settings override for eval paths and thresholds.
    """

    def __init__(
        self,
        pipeline,
        settings=None,
    ) -> None:
        self._pipeline = pipeline
        self._settings = settings

    async def run_full_evaluation(
        self,
        dataset=None,
        dataset_path: str | None = None,
        k_values: list[int] | None = None,
        generate_report: bool = True,
        compare_baseline: bool = True,
    ) -> EvaluationReport:
        """Execute the complete evaluation pipeline.

        Flow:
            1. Load dataset (from param or default path).
            2. For each query:
                a. Run pipeline.ask() to get predictions.
                b. Collect predicted chunk IDs from sources.
                c. Collect generated answer text.
            3. Compute retrieval metrics (precision@K, recall@K, MRR, MAP).
            4. Compute response quality (BLEU, ROUGE) for queries with references.
            5. Run latency benchmark on dataset queries.
            6. Load baseline and compare (if compare_baseline=True).
            7. Generate HTML report (if generate_report=True).
            8. Return assembled EvaluationReport.
        """
        # Import here to avoid circular imports at module level
        from datetime import datetime, timezone

        from mrag.config import get_settings
        from mrag.evaluation.baseline import (
            compare_to_baseline,
            load_baseline,
        )
        from mrag.evaluation.benchmarks import run_benchmark
        from mrag.evaluation.dataset_loader import load_evaluation_dataset
        from mrag.evaluation.models import (
            ResponseQualityMetrics,
            RetrievalMetrics,
        )
        from mrag.evaluation.report_generator import generate_report as gen_report
        from mrag.evaluation.response_metrics import compute_bleu, compute_rouge
        from mrag.evaluation.retrieval_metrics import (
            mean_average_precision,
            mean_reciprocal_rank,
            precision_at_k,
            recall_at_k,
        )

        settings = self._settings or get_settings()

        # 1. Load dataset
        path = dataset_path or settings.eval_heldout_path
        if dataset is None:
            dataset = load_evaluation_dataset(path)

        k_vals = k_values or settings.eval_k_values

        # 2. Run each query through the pipeline
        all_rankings: list[list[str]] = []
        all_relevants: list[set[str]] = []
        predictions: list[str] = []
        references: list[str] = []

        for query in dataset.queries:
            response = await self._pipeline.ask(query=query.question)
            predicted_ids = [s.chunk_id for s in response.sources]
            all_rankings.append(predicted_ids)
            all_relevants.append(query.relevant_chunk_ids)

            if query.reference_answer:
                predictions.append(response.answer)
                references.append(query.reference_answer)

        # 3. Compute retrieval metrics
        precision_k = {
            k: precision_at_k(all_rankings, all_relevants, k) for k in k_vals
        }
        recall_k = {k: recall_at_k(all_rankings, all_relevants, k) for k in k_vals}
        mrr = mean_reciprocal_rank(all_rankings, all_relevants)
        map_score = mean_average_precision(all_rankings, all_relevants)

        retrieval = RetrievalMetrics(
            precision_at_k=precision_k,
            recall_at_k=recall_k,
            mrr=mrr,
            map=map_score,
            num_queries=len(dataset.queries),
        )

        # 4. Compute response quality
        bleu = 0.0
        rouge_scores = {"rouge_1": 0.0, "rouge_2": 0.0, "rouge_l": 0.0}
        num_pairs = len(predictions)
        if predictions and references:
            bleu = compute_bleu(predictions, references)
            rouge_scores = compute_rouge(predictions, references)

        response_quality = ResponseQualityMetrics(
            bleu=bleu,
            rouge_1=rouge_scores["rouge_1"],
            rouge_2=rouge_scores["rouge_2"],
            rouge_l=rouge_scores["rouge_l"],
            num_pairs=max(num_pairs, 1),
        )

        # 5. Benchmark
        benchmark_queries = [q.question for q in dataset.queries][
            : settings.eval_benchmark_workload_size
        ]
        benchmark = await run_benchmark(self._pipeline, benchmark_queries)

        # 6. Baseline comparison
        baseline_comparison = None
        if compare_baseline:
            baseline = load_baseline(settings.eval_baseline_path)
            if baseline is not None:
                report_for_compare = EvaluationReport(
                    generated_at=datetime.now(timezone.utc).isoformat(),
                    mrag_version=settings.app_version,
                    dataset_name=dataset.name,
                    retrieval=retrieval,
                    response_quality=response_quality,
                    benchmark=benchmark,
                )
                baseline_comparison = compare_to_baseline(
                    report_for_compare,
                    baseline,
                    threshold_pct=settings.eval_regression_threshold,
                )

        # Build report
        now = datetime.now(timezone.utc)
        report = EvaluationReport(
            generated_at=now.isoformat(),
            mrag_version=settings.app_version,
            dataset_name=dataset.name,
            retrieval=retrieval,
            response_quality=response_quality,
            benchmark=benchmark,
            baseline_comparison=baseline_comparison,
        )

        # 7. Generate HTML report
        if generate_report:
            report_path = gen_report(report, settings.eval_report_dir)
            report.report_path = report_path

        return report
