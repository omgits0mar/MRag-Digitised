"""Data processing pipeline orchestration for MRAG.

Orchestrates the full data processing pipeline:
ingest → chunk → enrich → export with validation at each boundary.
"""

from __future__ import annotations

import time
from pathlib import Path

import structlog

from mrag.config import Settings, get_settings
from mrag.data.chunking import TextChunker
from mrag.data.enrichment import enrich
from mrag.data.export import export_jsonl
from mrag.data.ingestion import load_dataset
from mrag.data.models import AnswerType, PipelineResult, ProcessedDocument
from mrag.exceptions import DataProcessingError

logger = structlog.get_logger(__name__)


def run_pipeline(config: Settings | None = None) -> PipelineResult:
    """Orchestrate the full data processing pipeline.

    Args:
        config: Application settings. Uses get_settings() if None.

    Returns:
        PipelineResult with statistics.

    Raises:
        DataProcessingError: For unrecoverable failures.
    """
    if config is None:
        config = get_settings()

    start_time = time.time()
    logger.info("pipeline_starting")

    # Stage 1: Ingest
    raw_path = Path(config.data_dir) / "raw"
    csv_files = list(raw_path.glob("*.csv"))
    json_files = list(raw_path.glob("*.json"))

    all_files = [(str(f), "csv") for f in csv_files] + [
        (str(f), "json") for f in json_files
    ]

    if not all_files:
        raise DataProcessingError(
            "No dataset files found in data/raw/",
            detail={"data_dir": str(raw_path)},
        )

    total_skipped = 0
    from mrag.data.models import RawRecord

    all_records: list[RawRecord] = []
    for file_path, file_format in all_files:
        records, skipped = load_dataset(file_path, file_format)
        all_records.extend(records)
        total_skipped += skipped

    total_records = len(all_records) + total_skipped
    logger.info(
        "ingest_complete",
        total_records=total_records,
        valid=len(all_records),
        skipped=total_skipped,
    )

    # Stage 2: Chunk
    chunker = TextChunker(
        chunk_size=config.chunk_size,
        chunk_overlap=config.chunk_overlap,
    )

    # Stage 3: Enrich + build ProcessedDocuments
    processed_docs: list[ProcessedDocument] = []
    total_chunks = 0

    for raw in all_records:
        # Chunk the long answer
        chunks = chunker.chunk(raw.long_answers, doc_id="placeholder")

        # Enrich metadata
        metadata = enrich(
            question=raw.question,
            answer_short=raw.short_answers,
            answer_long=raw.long_answers,
        )

        # Determine answer type
        has_short = raw.short_answers is not None and raw.short_answers.strip() != ""
        answer_type = AnswerType.BOTH if has_short else AnswerType.LONG

        doc = ProcessedDocument(
            question=raw.question,
            answer_short=raw.short_answers,
            answer_long=raw.long_answers,
            answer_type=answer_type,
            chunks=chunks,
            metadata=metadata,
        )

        # Update chunk doc_ids and chunk_ids to match actual doc_id
        updated_chunks = []
        for i, chunk in enumerate(doc.chunks):
            updated_chunks.append(
                chunk.model_copy(
                    update={
                        "doc_id": doc.doc_id,
                        "chunk_id": f"{doc.doc_id}_chunk_{i}",
                    }
                )
            )
        doc = doc.model_copy(update={"chunks": updated_chunks})

        processed_docs.append(doc)
        total_chunks += len(doc.chunks)

    logger.info(
        "enrich_complete",
        documents=len(processed_docs),
        total_chunks=total_chunks,
    )

    # Stage 4: Export
    output_dir = str(Path(config.data_dir) / "processed")
    train_file, eval_file = export_jsonl(processed_docs, output_dir)

    elapsed = time.time() - start_time

    with open(train_file) as tf:
        train_count = sum(1 for _ in tf)
    with open(eval_file) as ef:
        eval_count = sum(1 for _ in ef)

    result = PipelineResult(
        total_records=total_records,
        valid_records=len(processed_docs),
        skipped_records=total_skipped,
        total_chunks=total_chunks,
        train_count=train_count,
        eval_count=eval_count,
        train_file=train_file,
        eval_file=eval_file,
        elapsed_seconds=elapsed,
    )

    logger.info(
        "pipeline_complete",
        total_records=result.total_records,
        valid_records=result.valid_records,
        total_chunks=result.total_chunks,
        elapsed_seconds=result.elapsed_seconds,
    )

    return result


if __name__ == "__main__":
    _mod = __import__("mrag.logging", fromlist=["configure_logging"])
    _mod.configure_logging()
    result = run_pipeline()
    print(
        f"Pipeline complete: {result.valid_records} records, "
        f"{result.total_chunks} chunks"
    )
