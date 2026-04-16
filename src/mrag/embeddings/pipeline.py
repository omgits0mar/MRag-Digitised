"""Embedding pipeline orchestration for MRAG.

Orchestrates: load JSONL -> embed -> build index -> save metadata.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import structlog

from mrag.config import Settings, get_settings
from mrag.embeddings.encoder import EmbeddingEncoder
from mrag.embeddings.indexer import FAISSIndexer
from mrag.embeddings.metadata_store import MetadataStore
from mrag.exceptions import EmbeddingError

logger = structlog.get_logger(__name__)


class EmbeddingPipelineResult:
    """Statistics from an embedding pipeline run."""

    def __init__(
        self,
        chunks_embedded: int,
        index_size: int,
        elapsed_seconds: float,
    ) -> None:
        self.chunks_embedded = chunks_embedded
        self.index_size = index_size
        self.elapsed_seconds = elapsed_seconds


def run_embedding_pipeline(
    config: Settings | None = None,
    input_file: str | None = None,
) -> EmbeddingPipelineResult:
    """Orchestrate the embedding pipeline: load JSONL -> embed -> index -> save.

    Args:
        config: Application settings. Uses get_settings() if None.
        input_file: Path to JSONL from data processing pipeline. Defaults to
            data/processed/train.jsonl.

    Returns:
        EmbeddingPipelineResult with statistics.

    Raises:
        EmbeddingError: If pipeline fails.
    """
    if config is None:
        config = get_settings()

    if input_file is None:
        input_file = str(Path(config.data_dir) / "processed" / "train.jsonl")

    start_time = time.time()
    logger.info("embedding_pipeline_starting", input_file=input_file)

    # Load processed documents from JSONL
    docs = _load_jsonl(input_file)
    if not docs:
        raise EmbeddingError("No documents found in input file")

    # Extract chunk texts and metadata
    chunk_texts: list[str] = []
    metadata_entries: list[dict[str, Any]] = []

    for doc in docs:
        doc_id = doc["doc_id"]
        question = doc["question"]
        answer_short = doc.get("answer_short")
        answer_long = doc["answer_long"]
        meta = doc.get("metadata", {})

        for chunk in doc.get("chunks", []):
            chunk_texts.append(chunk["text"])
            metadata_entries.append(
                {
                    "chunk_id": chunk["chunk_id"],
                    "doc_id": doc_id,
                    "chunk_text": chunk["text"],
                    "question": question,
                    "answer_short": answer_short,
                    "answer_long": answer_long,
                    "question_type": meta.get("question_type", "unknown"),
                    "domain": meta.get("domain", "general"),
                    "difficulty": meta.get("difficulty", "medium"),
                    "has_short_answer": meta.get("has_short_answer", False),
                }
            )

    logger.info("chunks_extracted", count=len(chunk_texts))

    # Embed all chunks
    encoder = EmbeddingEncoder(model_name=config.embedding_model_name)
    embeddings = encoder.encode(chunk_texts, batch_size=64)

    # Build FAISS index
    indexer = FAISSIndexer(dimension=config.embedding_dimension)
    indexer.build_index(embeddings)

    # Build metadata store
    metadata_store = MetadataStore()
    for i, meta in enumerate(metadata_entries):
        metadata_store.add(faiss_id=i, **meta)

    # Save artifacts
    output_dir = Path(config.data_dir) / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)

    index_path = str(output_dir / "index.faiss")
    metadata_path = str(output_dir / "metadata.json")

    indexer.save(index_path)
    metadata_store.save(metadata_path)

    elapsed = time.time() - start_time
    result = EmbeddingPipelineResult(
        chunks_embedded=len(chunk_texts),
        index_size=indexer.ntotal,
        elapsed_seconds=elapsed,
    )

    logger.info(
        "embedding_pipeline_complete",
        chunks_embedded=result.chunks_embedded,
        index_size=result.index_size,
        elapsed_seconds=result.elapsed_seconds,
    )

    return result


def _load_jsonl(path: str) -> list[dict[str, Any]]:
    """Load JSONL file into a list of dicts."""
    docs: list[dict[str, Any]] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                docs.append(json.loads(line))
    return docs


if __name__ == "__main__":
    from mrag.logging import configure_logging

    configure_logging()
    result = run_embedding_pipeline()
    print(
        f"Embedding pipeline complete: {result.chunks_embedded} chunks, "
        f"{result.index_size} indexed, {result.elapsed_seconds:.1f}s"
    )
