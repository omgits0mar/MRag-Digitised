"""Parser registry mapping file extensions to parser callables."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ParsedDocument:
    """One logical document parsed out of an uploaded file.

    Attributes:
        doc_id: Stable identifier for this logical document.
        text: Raw UTF-8 text extracted by the parser.
        source_filename: Original uploaded filename (for metadata/provenance).
        section: Optional section label (e.g. "page 3", "row 17").
    """

    doc_id: str
    text: str
    source_filename: str
    section: str | None = None


class ParserError(Exception):
    """Raised when a parser fails to read its input."""


class UnsupportedExtensionError(ParserError):
    """Raised when no parser is registered for the given extension."""


Parser = Callable[[Path, str], Iterable[ParsedDocument]]


def _normalize_extension(ext: str) -> str:
    return ext.strip().lstrip(".").lower()


def _get_registry() -> dict[str, Parser]:
    """Lazy-build the parser registry.

    Imports are done on first call to avoid importing heavy PDF/DOCX
    libraries at module import time.
    """
    from mrag.data.parsers.csv import parse_csv
    from mrag.data.parsers.docx import parse_docx
    from mrag.data.parsers.md import parse_markdown
    from mrag.data.parsers.pdf import parse_pdf
    from mrag.data.parsers.txt import parse_txt

    return {
        "txt": parse_txt,
        "md": parse_markdown,
        "csv": parse_csv,
        "pdf": parse_pdf,
        "docx": parse_docx,
    }


def supported_extensions() -> list[str]:
    """Return the list of supported file extensions (lowercase, no dot)."""
    return sorted(_get_registry().keys())


def parse_file(path: Path, source_filename: str) -> list[ParsedDocument]:
    """Parse a file into one or more ParsedDocument records.

    Args:
        path: Path to the file on disk.
        source_filename: Original filename (used for provenance in results).

    Returns:
        Non-empty list of ParsedDocument. Documents with empty/whitespace-only
        text are dropped.

    Raises:
        UnsupportedExtensionError: If the extension is not registered.
        ParserError: If the parser fails.
    """
    ext = _normalize_extension(path.suffix)
    registry = _get_registry()
    parser = registry.get(ext)
    if parser is None:
        raise UnsupportedExtensionError(
            f"No parser registered for extension '.{ext}'"
        )

    docs = [d for d in parser(path, source_filename) if d.text and d.text.strip()]
    if not docs:
        raise ParserError(
            f"Parser produced no text for '{source_filename}'"
        )
    return docs
