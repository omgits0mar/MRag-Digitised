"""Tests for the chunker registry and RowChunker."""

from __future__ import annotations

from mrag.data.chunking import (
    RowChunker,
    SentenceWindowChunker,
    TextChunker,
    get_chunker,
)
from mrag.data.parsers.registry import ParsedDocument


def test_get_chunker_returns_row_chunker_for_csv() -> None:
    chunker = get_chunker("csv", chunk_size=256, chunk_overlap=32)
    assert isinstance(chunker, RowChunker)


def test_get_chunker_returns_sentence_window_for_prose() -> None:
    for ext in ("txt", "md", "pdf", "docx"):
        chunker = get_chunker(ext)
        assert isinstance(chunker, TextChunker)


def test_sentence_window_chunker_is_text_chunker_alias() -> None:
    assert SentenceWindowChunker is TextChunker


def test_row_chunker_one_chunk_per_doc() -> None:
    chunker = RowChunker(chunk_size=512, chunk_overlap=50)
    docs = [
        ParsedDocument(
            doc_id=f"doc-{i}",
            text=f"row {i} content",
            source_filename="x.csv",
            section=f"row {i + 1}",
        )
        for i in range(3)
    ]
    chunks = chunker.chunk_documents(docs)
    assert len(chunks) == 3
    assert all(c.chunk_index == 0 and c.total_chunks == 1 for c in chunks)
    assert chunks[0].doc_id == "doc-0"


def test_row_chunker_falls_back_for_oversize_rows() -> None:
    chunker = RowChunker(chunk_size=10, chunk_overlap=2)
    # Use sentence punctuation so the sentence-window fallback can split it.
    long_text = ". ".join(
        " ".join(f"word{j}" for j in range(i * 5, i * 5 + 5)) for i in range(10)
    ) + "."
    docs = [
        ParsedDocument(
            doc_id="big",
            text=long_text,
            source_filename="big.csv",
            section="row 1",
        )
    ]
    chunks = chunker.chunk_documents(docs)
    assert len(chunks) > 1
    assert all(c.doc_id == "big" for c in chunks)
