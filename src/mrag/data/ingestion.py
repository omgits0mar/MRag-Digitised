"""Dataset ingestion and validation for MRAG.

Loads CSV/JSON datasets using Pandas, validates each record against
the RawRecord Pydantic model, and skips malformed rows with logging.
"""

from __future__ import annotations

import unicodedata
from pathlib import Path

import pandas as pd
import structlog

from mrag.data.models import RawRecord
from mrag.exceptions import DataProcessingError

logger = structlog.get_logger(__name__)


def load_dataset(
    file_path: str, file_format: str = "csv"
) -> tuple[list[RawRecord], int]:
    """Load and validate raw dataset from file.

    Args:
        file_path: Path to the raw dataset file (CSV or JSON).
        file_format: One of "csv" or "json".

    Returns:
        Tuple of (validated records, skipped count).

    Raises:
        DataProcessingError: If file not found, unreadable, or all records
            fail validation.
    """
    path = Path(file_path)
    if not path.exists():
        raise DataProcessingError(
            f"Dataset file not found: {file_path}",
            detail={"file_path": file_path},
        )

    logger.info("loading_dataset", file_path=file_path, format=file_format)

    try:
        if file_format == "csv":
            df = pd.read_csv(path, encoding="utf-8", dtype=str)
        elif file_format == "json":
            df = pd.read_json(path, encoding="utf-8", dtype=str)
        else:
            raise DataProcessingError(
                f"Unsupported file format: {file_format}",
                detail={"file_format": file_format},
            )
    except Exception as exc:
        raise DataProcessingError(
            f"Failed to read dataset: {exc}",
            detail={"file_path": file_path, "format": file_format},
        ) from exc

    if df.empty:
        raise DataProcessingError(
            "Dataset is empty",
            detail={"file_path": file_path},
        )

    records: list[RawRecord] = []
    skipped = 0

    for idx, row in df.iterrows():
        try:
            raw = _row_to_raw_record(row)
            records.append(raw)
        except Exception as exc:
            skipped += 1
            logger.warning(
                "skipping_malformed_record",
                row_index=idx,
                error=str(exc),
            )

    logger.info(
        "dataset_loaded",
        total_rows=len(df),
        valid_records=len(records),
        skipped_records=skipped,
    )

    if len(records) == 0 and len(df) > 0:
        raise DataProcessingError(
            f"All {len(df)} records failed validation",
            detail={
                "total_rows": len(df),
                "skipped": skipped,
                "file_path": file_path,
            },
        )

    return records, skipped


def _row_to_raw_record(row: pd.Series) -> RawRecord:
    """Convert a DataFrame row to a RawRecord with Unicode normalization.

    Columns match Natural-Questions-Filtered.csv: question, short_answers,
    long_answers.
    """
    question = row.get("question")
    long_answers = row.get("long_answers")
    short_answers = row.get("short_answers")

    # Handle NaN from Pandas
    question = _clean_pandas_value(question)
    long_answers = _clean_pandas_value(long_answers)
    short_answers = _clean_pandas_value(short_answers)

    if question is None or long_answers is None:
        raise ValueError("Missing required fields: question or long_answers")

    # Unicode NFC normalization
    question = unicodedata.normalize("NFC", question)
    long_answers = unicodedata.normalize("NFC", long_answers)
    if short_answers is not None:
        short_answers = unicodedata.normalize("NFC", short_answers)

    return RawRecord(
        question=question,
        short_answers=short_answers,
        long_answers=long_answers,
    )


def _clean_pandas_value(value: object) -> str | None:
    """Convert a Pandas value to str or None, handling NaN."""
    if value is None:
        return None
    if isinstance(value, float) and pd.isna(value):
        return None
    result = str(value).strip()
    return result if result else None
