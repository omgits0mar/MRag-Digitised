"""Plain-text file parser."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from uuid import uuid4

from mrag.data.parsers.registry import ParsedDocument, ParserError


def parse_txt(path: Path, source_filename: str) -> Iterable[ParsedDocument]:
    """Read a UTF-8 text file as a single ParsedDocument."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        raise ParserError(f"Failed to read text file: {exc}") from exc

    yield ParsedDocument(
        doc_id=str(uuid4()),
        text=text,
        source_filename=source_filename,
        section=None,
    )
