"""PDF parser using pypdf.

Emits one ParsedDocument per page so retrieval can cite the source page.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from uuid import uuid4

from mrag.data.parsers.registry import ParsedDocument, ParserError


def parse_pdf(path: Path, source_filename: str) -> Iterable[ParsedDocument]:
    """Extract text per page and yield one ParsedDocument per page."""
    try:
        from pypdf import PdfReader
    except ImportError as exc:  # pragma: no cover - dep is pinned
        raise ParserError(
            "pypdf is required to parse PDF files; install it to enable uploads"
        ) from exc

    try:
        reader = PdfReader(str(path))
    except Exception as exc:
        raise ParserError(f"Failed to open PDF: {exc}") from exc

    for page_index, page in enumerate(reader.pages):
        try:
            text = page.extract_text() or ""
        except Exception:
            text = ""
        if not text.strip():
            continue
        yield ParsedDocument(
            doc_id=str(uuid4()),
            text=text,
            source_filename=source_filename,
            section=f"page {page_index + 1}",
        )
