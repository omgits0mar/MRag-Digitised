"""JSON-backed metadata store for parallel storage alongside FAISS index.

Provides O(1) lookup by FAISS integer ID and field-value filtering.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

import structlog

from mrag.data.models import Difficulty, QuestionType

logger = structlog.get_logger(__name__)


class MetadataEntry:
    """Metadata stored alongside a FAISS index entry."""

    __slots__ = (
        "faiss_index_id",
        "chunk_id",
        "doc_id",
        "chunk_text",
        "question",
        "answer_short",
        "answer_long",
        "question_type",
        "domain",
        "difficulty",
        "has_short_answer",
    )

    def __init__(
        self,
        faiss_index_id: int,
        chunk_id: str,
        doc_id: str,
        chunk_text: str,
        question: str,
        answer_short: str | None,
        answer_long: str,
        question_type: QuestionType | str,
        domain: str,
        difficulty: Difficulty | str,
        has_short_answer: bool,
    ) -> None:
        self.faiss_index_id = faiss_index_id
        self.chunk_id = chunk_id
        self.doc_id = doc_id
        self.chunk_text = chunk_text
        self.question = question
        self.answer_short = answer_short
        self.answer_long = answer_long
        self.question_type = (
            question_type.value
            if isinstance(question_type, QuestionType)
            else question_type
        )
        self.domain = domain
        self.difficulty = (
            difficulty.value if isinstance(difficulty, Difficulty) else difficulty
        )
        self.has_short_answer = has_short_answer

    def to_dict(self) -> dict[str, Any]:
        return {
            "faiss_index_id": self.faiss_index_id,
            "chunk_id": self.chunk_id,
            "doc_id": self.doc_id,
            "chunk_text": self.chunk_text,
            "question": self.question,
            "answer_short": self.answer_short,
            "answer_long": self.answer_long,
            "question_type": self.question_type,
            "domain": self.domain,
            "difficulty": self.difficulty,
            "has_short_answer": self.has_short_answer,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MetadataEntry:
        return cls(**data)


class MetadataStore:
    """Parallel metadata storage keyed by FAISS integer ID.

    In-memory dict[int, MetadataEntry] with JSON persistence.
    """

    def __init__(self) -> None:
        self._entries: dict[int, MetadataEntry] = {}

    def add(self, faiss_id: int, **kwargs: Any) -> None:
        """Add a metadata entry."""
        entry = MetadataEntry(faiss_index_id=faiss_id, **kwargs)
        self._entries[faiss_id] = entry

    def add_entries(self, entries: list[MetadataEntry]) -> None:
        """Append prepared entries to the store, keyed by their FAISS index IDs."""
        for entry in entries:
            self._entries[entry.faiss_index_id] = entry

    def get(self, faiss_id: int) -> MetadataEntry:
        """Retrieve metadata by FAISS ID.

        Raises:
            KeyError: If ID not found.
        """
        if faiss_id not in self._entries:
            raise KeyError(f"Metadata not found for FAISS ID: {faiss_id}")
        return self._entries[faiss_id]

    def filter(self, field: str, value: str) -> list[int]:
        """Return FAISS IDs matching a metadata field value.

        Args:
            field: Metadata field name (e.g., "domain", "question_type").
            value: Value to match.

        Returns:
            List of matching FAISS integer IDs.
        """
        result = []
        for faiss_id, entry in self._entries.items():
            entry_value = getattr(entry, field, None)
            if entry_value is not None and str(entry_value) == str(value):
                result.append(faiss_id)
        return result

    def save(self, path: str) -> None:
        """Persist metadata to JSON file atomically (tmp + rename)."""
        parent = Path(path).parent
        parent.mkdir(parents=True, exist_ok=True)
        data = {str(k): v.to_dict() for k, v in self._entries.items()}
        fd, tmp_path = tempfile.mkstemp(
            prefix=".metadata_", suffix=".json.tmp", dir=str(parent)
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(tmp_path, path)
        except Exception:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            raise
        logger.info("metadata_saved", path=path, count=len(self._entries))

    def load(self, path: str) -> None:
        """Load metadata from JSON file.

        Raises:
            Exception: If file not found or invalid.
        """
        if not Path(path).exists():
            raise FileNotFoundError(f"Metadata file not found: {path}")

        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        self._entries = {}
        for key, entry_dict in data.items():
            faiss_id = int(key)
            self._entries[faiss_id] = MetadataEntry.from_dict(entry_dict)
        logger.info("metadata_loaded", path=path, count=len(self._entries))

    @property
    def size(self) -> int:
        """Number of entries in the store."""
        return len(self._entries)
