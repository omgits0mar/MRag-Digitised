"""Dataset loader for the evaluation framework.

Loads the Phase 1 eval split (data/processed/eval.jsonl) and converts
each ProcessedDocument to an EvaluationQuery.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import structlog

from mrag.evaluation.models import EvaluationDataset, EvaluationQuery
from mrag.exceptions import EvaluationError

logger = structlog.get_logger(__name__)


def load_evaluation_dataset(path: str) -> EvaluationDataset:
    """Load the held-out evaluation dataset from disk.

    Reads the Phase 1 eval split (default: data/processed/eval.jsonl)
    which contains ProcessedDocument JSONL records.

    For each ProcessedDocument:
        - query_id  <- doc.doc_id
        - question  <- doc.question
        - relevant_chunk_ids <- {chunk.chunk_id for chunk in doc.chunks}
        - reference_answer <- doc.answer_short (nullable)

    Args:
        path: Filesystem path to the JSONL file.

    Returns:
        EvaluationDataset with validated EvaluationQuery entries.

    Raises:
        FileNotFoundError: If path does not exist.
        EvaluationError: If no valid queries after loading.
    """
    queries: list[EvaluationQuery] = []
    skipped = 0

    with open(path, encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                doc = json.loads(line)
                query = EvaluationQuery(
                    query_id=doc["doc_id"],
                    question=doc["question"],
                    relevant_chunk_ids={
                        chunk["chunk_id"] for chunk in doc.get("chunks", [])
                    },
                    reference_answer=doc.get("answer_short"),
                )
                queries.append(query)
            except (json.JSONDecodeError, KeyError, Exception) as exc:
                skipped += 1
                logger.warning(
                    "eval_dataset_skip_row",
                    line=line_num,
                    error=str(exc),
                )

    if not queries:
        raise EvaluationError(
            f"No valid queries loaded from {path}",
            detail={"skipped": skipped},
        )

    if skipped > 0:
        logger.warning(
            "eval_dataset_rows_skipped",
            skipped=skipped,
            loaded=len(queries),
        )

    return EvaluationDataset(
        name=f"eval_{Path(path).stem}",
        queries=queries,
        created_at=datetime.now(timezone.utc).isoformat(),
    )
