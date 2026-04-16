"""Integration tests for UploadService end-to-end ingestion."""

from __future__ import annotations

import io
from pathlib import Path

import numpy as np
import pytest

from mrag.embeddings.indexer import FAISSIndexer
from mrag.embeddings.metadata_store import MetadataStore
from mrag.ingestion.upload_service import (
    FileTooLargeError,
    UploadIngestionError,
    UploadService,
)


class StubEncoder:
    """Deterministic stand-in for EmbeddingEncoder that avoids loading a model."""

    def __init__(self, dim: int = 8) -> None:
        self._dim = dim

    def encode(self, texts: list[str], batch_size: int = 64) -> np.ndarray:
        rng = np.random.RandomState(len(texts))
        vecs = rng.randn(len(texts), self._dim).astype(np.float32)
        vecs /= np.linalg.norm(vecs, axis=1, keepdims=True) + 1e-9
        return vecs

    def encode_single(self, text: str) -> np.ndarray:
        return self.encode([text])[0]


def _build_service(tmp_path: Path, max_bytes: int = 1_000_000) -> UploadService:
    return UploadService(
        encoder=StubEncoder(dim=8),
        indexer=FAISSIndexer(dimension=8),
        metadata_store=MetadataStore(),
        upload_dir=tmp_path / "uploads",
        index_path=tmp_path / "index.faiss",
        metadata_path=tmp_path / "metadata.json",
        max_bytes=max_bytes,
        allowed_extensions=["txt", "csv", "md", "docx"],
        chunk_size=64,
        chunk_overlap=8,
    )


class AsyncFileLike:
    """Minimal FastAPI-UploadFile-like stub that exposes async ``read``."""

    def __init__(self, data: bytes) -> None:
        self._buf = io.BytesIO(data)

    async def read(self, n: int) -> bytes:
        return self._buf.read(n)


@pytest.mark.asyncio
async def test_ingest_text_file_adds_vectors_and_persists(tmp_path: Path) -> None:
    service = _build_service(tmp_path)
    payload = (
        b"The capital of Burkina Faso is Ouagadougou.\n"
        b"It is a West African country."
    )
    stream = AsyncFileLike(payload)

    saved = await service.save_stream(stream, "facts.txt")
    assert saved.exists()
    result = await service.ingest(saved, "facts.txt")

    assert result.extension == "txt"
    assert result.chunks_added >= 1
    assert result.total_vectors == result.chunks_added
    assert (tmp_path / "index.faiss").exists()
    assert (tmp_path / "metadata.json").exists()
    assert service.last_result is not None


@pytest.mark.asyncio
async def test_save_stream_enforces_max_bytes(tmp_path: Path) -> None:
    service = _build_service(tmp_path, max_bytes=10)
    stream = AsyncFileLike(b"x" * 100)
    with pytest.raises(FileTooLargeError):
        await service.save_stream(stream, "big.txt")
    # Oversize file should not remain on disk
    leftover = list((tmp_path / "uploads").iterdir())
    assert leftover == []


@pytest.mark.asyncio
async def test_unsupported_extension_rejected(tmp_path: Path) -> None:
    service = _build_service(tmp_path)
    with pytest.raises(UploadIngestionError):
        service.validate_extension("payload.exe")


@pytest.mark.asyncio
async def test_csv_upload_produces_row_chunks(tmp_path: Path) -> None:
    service = _build_service(tmp_path)
    payload = b"title,body\nFoo,alpha text\nBar,beta text\nBaz,gamma text\n"
    stream = AsyncFileLike(payload)
    saved = await service.save_stream(stream, "rows.csv")
    result = await service.ingest(saved, "rows.csv")
    assert result.chunks_added == 3
    assert result.total_vectors == 3
