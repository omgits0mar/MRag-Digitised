"""Markdown file parser.

Strips YAML front-matter and common markdown formatting markers so the
retrieved text is closer to what a reader actually sees.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from pathlib import Path
from uuid import uuid4

from mrag.data.parsers.registry import ParsedDocument, ParserError

_FRONTMATTER_RE = re.compile(r"^---\s*\n.*?\n---\s*\n", re.DOTALL)
_CODE_FENCE_RE = re.compile(r"```.*?```", re.DOTALL)
_INLINE_CODE_RE = re.compile(r"`([^`]+)`")
_LINK_RE = re.compile(r"\[([^\]]+)\]\([^)]+\)")
_IMAGE_RE = re.compile(r"!\[[^\]]*\]\([^)]+\)")
_HEADING_RE = re.compile(r"^#{1,6}\s*", re.MULTILINE)
_EMPHASIS_RE = re.compile(r"(\*\*|__|\*|_)(.+?)\1")


def _strip_markdown(text: str) -> str:
    text = _FRONTMATTER_RE.sub("", text, count=1)
    text = _IMAGE_RE.sub("", text)
    text = _CODE_FENCE_RE.sub(" ", text)
    text = _INLINE_CODE_RE.sub(r"\1", text)
    text = _LINK_RE.sub(r"\1", text)
    text = _HEADING_RE.sub("", text)
    text = _EMPHASIS_RE.sub(r"\2", text)
    return text


def parse_markdown(path: Path, source_filename: str) -> Iterable[ParsedDocument]:
    """Read a markdown file, strip front-matter and formatting, emit one doc."""
    try:
        raw = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        raise ParserError(f"Failed to read markdown file: {exc}") from exc

    text = _strip_markdown(raw)

    yield ParsedDocument(
        doc_id=str(uuid4()),
        text=text,
        source_filename=source_filename,
        section=None,
    )
