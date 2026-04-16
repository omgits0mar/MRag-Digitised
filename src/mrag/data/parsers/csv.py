"""CSV file parser.

Emits one ParsedDocument per non-empty row. Columns are joined as
``"<column>: <value>"`` pairs so retrieval sees labelled context.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from uuid import uuid4

import pandas as pd

from mrag.data.parsers.registry import ParsedDocument, ParserError


def _row_to_text(row: pd.Series) -> str:
    parts: list[str] = []
    for col, value in row.items():
        if value is None:
            continue
        if isinstance(value, float) and pd.isna(value):
            continue
        text = str(value).strip()
        if not text:
            continue
        parts.append(f"{col}: {text}")
    return " | ".join(parts)


def parse_csv(path: Path, source_filename: str) -> Iterable[ParsedDocument]:
    """Read a CSV file and yield one ParsedDocument per row."""
    try:
        df = pd.read_csv(path, dtype=str, keep_default_na=False)
    except Exception as exc:  # pandas raises various errors on malformed input
        raise ParserError(f"Failed to parse CSV: {exc}") from exc

    for i, row in df.iterrows():
        text = _row_to_text(row)
        if not text:
            continue
        yield ParsedDocument(
            doc_id=str(uuid4()),
            text=text,
            source_filename=source_filename,
            section=f"row {int(i) + 1}",
        )
