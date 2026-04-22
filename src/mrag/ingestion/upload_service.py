"""Upload ingestion service.

Parses a user-uploaded file, chunks it with the appropriate strategy,
embeds the chunks, and appends them to the live FAISS index and
metadata store. Persists both stores to disk so restarts retain the
uploaded content.
"""

from __future__ import annotations

import asyncio
import contextlib
import re
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO

import structlog

from mrag.cache.response_cache import ResponseCache
from mrag.data.chunking import get_chunker
from mrag.data.models import TextChunk
from mrag.data.parsers import ParsedDocument, parse_file
from mrag.embeddings.encoder import EmbeddingEncoder
from mrag.embeddings.indexer import FAISSIndexer
from mrag.embeddings.metadata_store import MetadataEntry, MetadataStore

logger = structlog.get_logger(__name__)


class UploadIngestionError(Exception):
    """Raised when an upload cannot be ingested."""


class FileTooLargeError(UploadIngestionError):
    """Raised when a streamed upload exceeds the configured size cap."""


@dataclass
class UploadResult:
    """Outcome of a successful upload ingestion."""

    filename: str
    extension: str
    chunks_added: int
    total_vectors: int
    ingested_at: float

    def to_dict(self) -> dict[str, object]:
        return {
            "filename": self.filename,
            "extension": self.extension,
            "chunks_added": self.chunks_added,
            "total_vectors": self.total_vectors,
            "ingested_at": self.ingested_at,
        }


_SAFE_FILENAME_RE = re.compile(r"[^A-Za-z0-9._-]+")


def _sanitize_filename(filename: str) -> str:
    """Strip directory traversal and replace unsafe chars."""
    base = Path(filename).name  # drop any path components
    base = _SAFE_FILENAME_RE.sub("_", base).strip("._") or "upload"
    return base[:200]


class UploadService:
    """Handles saving uploaded files and ingesting them into the index.

    Streaming save enforces a byte cap before the full file is read into
    memory. An asyncio lock serializes the FAISS mutation step because
    ``IndexFlatIP.add`` is not thread-safe.

    Args:
        encoder: Embedding encoder shared with the retrieval pipeline.
        indexer: FAISSIndexer shared with the retrieval pipeline.
        metadata_store: MetadataStore shared with the retrieval pipeline.
        upload_dir: Directory where raw uploads are persisted.
        index_path: File path for the FAISS index (.faiss).
        metadata_path: File path for the metadata JSON.
        max_bytes: Maximum allowed upload size in bytes.
        allowed_extensions: Accepted lowercase extensions (no dot).
        chunk_size / chunk_overlap: Chunker configuration.
        response_cache: Optional response cache cleared after ingest so
            previously cached answers don't mask newly indexed content.
    """

    def __init__(
        self,
        *,
        encoder: EmbeddingEncoder,
        indexer: FAISSIndexer,
        metadata_store: MetadataStore,
        upload_dir: Path,
        index_path: Path,
        metadata_path: Path,
        max_bytes: int,
        allowed_extensions: list[str],
        chunk_size: int,
        chunk_overlap: int,
        response_cache: ResponseCache | None = None,
    ) -> None:
        self._encoder = encoder
        self._indexer = indexer
        self._metadata_store = metadata_store
        self._upload_dir = upload_dir
        self._index_path = index_path
        self._metadata_path = metadata_path
        self._max_bytes = max_bytes
        self._allowed = {ext.lower().lstrip(".") for ext in allowed_extensions}
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap
        self._response_cache = response_cache
        self._mutex = asyncio.Lock()
        self._last_result: UploadResult | None = None
        self._upload_dir.mkdir(parents=True, exist_ok=True)

    @property
    def allowed_extensions(self) -> list[str]:
        return sorted(self._allowed)

    @property
    def max_bytes(self) -> int:
        return self._max_bytes

    @property
    def last_result(self) -> UploadResult | None:
        return self._last_result

    @property
    def total_vectors(self) -> int:
        return self._indexer.ntotal

    def validate_extension(self, filename: str) -> str:
        """Return the normalized extension or raise if it is not allowed."""
        ext = Path(filename).suffix.lstrip(".").lower()
        if not ext or ext not in self._allowed:
            raise UploadIngestionError(
                f"Unsupported file extension '.{ext}'. "
                f"Allowed: {sorted(self._allowed)}"
            )
        return ext

    async def save_stream(
        self,
        stream: BinaryIO,
        filename: str,
        read_chunk: int = 1024 * 1024,
    ) -> Path:
        """Stream ``stream`` to disk under ``upload_dir`` with size enforcement.

        ``stream`` must expose an async ``read(n)`` method (FastAPI's
        ``UploadFile.read`` works) OR a sync one — both are handled.

        Raises:
            FileTooLargeError: When cumulative bytes exceed ``max_bytes``.
        """
        safe = _sanitize_filename(filename)
        target = self._upload_dir / f"{uuid.uuid4().hex}_{safe}"
        total = 0
        try:
            with target.open("wb") as out:
                while True:
                    data = await _maybe_await(stream.read(read_chunk))
                    if not data:
                        break
                    total += len(data)
                    if total > self._max_bytes:
                        raise FileTooLargeError(
                            f"Upload exceeds max size of {self._max_bytes} bytes"
                        )
                    out.write(data)
        except Exception:
            if target.exists():
                with contextlib.suppress(OSError):
                    target.unlink()
            raise
        return target

    async def ingest(self, file_path: Path, original_filename: str) -> UploadResult:
        """Parse, chunk, embed, and index a saved file."""
        ext = self.validate_extension(original_filename)

        async with self._mutex:
            result = await asyncio.to_thread(
                self._ingest_sync, file_path, original_filename, ext
            )
            if self._response_cache is not None:
                self._response_cache.clear()
            self._last_result = result
            return result

    # ------------------------------------------------------------------ sync

    def _ingest_sync(
        self, file_path: Path, original_filename: str, ext: str
    ) -> UploadResult:
        parsed: list[ParsedDocument] = parse_file(file_path, original_filename)
        chunker = get_chunker(
            ext,
            chunk_size=self._chunk_size,
            chunk_overlap=self._chunk_overlap,
        )
        chunks: list[TextChunk] = chunker.chunk_documents(parsed)
        if not chunks:
            raise UploadIngestionError(
                f"No chunks produced from '{original_filename}'"
            )

        texts = [c.text for c in chunks]
        vectors = self._encoder.encode(texts)
        assigned_ids = self._indexer.add_vectors(vectors)

        doc_id_to_parsed = {p.doc_id: p for p in parsed}
        entries: list[MetadataEntry] = []
        for faiss_id, chunk in zip(assigned_ids, chunks, strict=True):
            parent = doc_id_to_parsed.get(chunk.doc_id)
            section = parent.section if parent else None
            domain = f"upload:{ext}"
            if section:
                domain = f"{domain}:{section}"
            entries.append(
                MetadataEntry(
                    faiss_index_id=faiss_id,
                    chunk_id=chunk.chunk_id,
                    doc_id=chunk.doc_id,
                    chunk_text=chunk.text,
                    question=original_filename,
                    answer_short=None,
                    answer_long=chunk.text,
                    question_type="unknown",
                    domain=domain,
                    difficulty="medium",
                    has_short_answer=False,
                )
            )

        self._metadata_store.add_entries(entries)
        self._indexer.save(str(self._index_path))
        self._metadata_store.save(str(self._metadata_path))

        logger.info(
            "upload_ingested",
            filename=original_filename,
            chunks_added=len(chunks),
            total_vectors=self._indexer.ntotal,
        )
        return UploadResult(
            filename=original_filename,
            extension=ext,
            chunks_added=len(chunks),
            total_vectors=self._indexer.ntotal,
            ingested_at=time.time(),
        )


async def _maybe_await(value):
    """Await ``value`` if it is awaitable, else return it unchanged."""
    if asyncio.iscoroutine(value):
        return await value
    return value
