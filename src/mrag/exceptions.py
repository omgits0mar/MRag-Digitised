"""Shared exception hierarchy for MRAG.

Provides a base MRAGError and module-specific subclasses for uniform error
handling across all modules.
"""

from __future__ import annotations

from typing import Any


class MRAGError(Exception):
    """Base exception for all MRAG project errors.

    Attributes:
        message: Human-readable error description.
        detail: Optional structured context for debugging / API responses.
    """

    def __init__(self, message: str, detail: dict[str, Any] | None = None) -> None:
        self.message = message
        self.detail = detail
        super().__init__(message)

    def __str__(self) -> str:
        return self.message


class DataProcessingError(MRAGError):
    """Errors in dataset loading, parsing, or chunking."""


class EmbeddingError(MRAGError):
    """Errors in embedding model loading or inference."""


class RetrievalError(MRAGError):
    """Errors in vector search or index loading."""


class QueryProcessingError(MRAGError):
    """Errors in query parsing or expansion."""


class ResponseGenerationError(MRAGError):
    """Errors in LLM calls or response validation."""


class CacheError(MRAGError):
    """Errors in cache read/write or invalidation."""


class APIError(MRAGError):
    """Errors in request validation or endpoints."""


class DatabaseError(MRAGError):
    """Errors in database connections, queries, or migrations."""


class EvaluationError(MRAGError):
    """Errors in metric computation or benchmarks."""
