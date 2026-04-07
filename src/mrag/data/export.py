"""JSONL export with deterministic train/eval split for MRAG.

Exports processed documents to JSON Lines format with a reproducible
train/evaluation split based on a fixed random seed.
"""

from __future__ import annotations

from pathlib import Path

import structlog

from mrag.data.models import ProcessedDocument

logger = structlog.get_logger(__name__)


def export_jsonl(
    documents: list[ProcessedDocument],
    output_dir: str,
    split_ratio: float = 0.9,
    seed: int = 42,
) -> tuple[str, str]:
    """Export processed documents to JSONL with train/eval split.

    Args:
        documents: Fully processed documents.
        output_dir: Directory for output files.
        split_ratio: Fraction for training set (default 0.9).
        seed: Random seed for reproducible split.

    Returns:
        Tuple of (train_file_path, eval_file_path).
    """
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    # Deterministic split: sort by doc_id, then use modular split
    sorted_docs = sorted(documents, key=lambda d: d.doc_id)

    # Use a simple deterministic split based on hash of doc_id + seed
    train_docs: list[ProcessedDocument] = []
    eval_docs: list[ProcessedDocument] = []

    # Simple seeded split: use doc_id hash with seed
    import hashlib

    for doc in sorted_docs:
        key = f"{doc.doc_id}:{seed}"
        h = int(hashlib.md5(key.encode()).hexdigest(), 16)
        if (h % 100) < int(split_ratio * 100):
            train_docs.append(doc)
        else:
            eval_docs.append(doc)

    train_file = str(out_path / "train.jsonl")
    eval_file = str(out_path / "eval.jsonl")

    _write_jsonl(train_file, train_docs)
    _write_jsonl(eval_file, eval_docs)

    logger.info(
        "export_complete",
        total=len(documents),
        train_count=len(train_docs),
        eval_count=len(eval_docs),
        train_file=train_file,
        eval_file=eval_file,
    )

    return train_file, eval_file


def _write_jsonl(path: str, docs: list[ProcessedDocument]) -> None:
    """Write a list of ProcessedDocuments to a JSONL file."""
    with open(path, "w", encoding="utf-8") as f:
        for doc in docs:
            f.write(doc.model_dump_json() + "\n")
