"""Query preprocessing: unicode normalization, case folding, whitespace collapse.

Handles multilingual input via NFC normalization so that visually-identical
but differently-encoded strings collapse to the same form.
"""

from __future__ import annotations

import re
import unicodedata

import structlog

from mrag.exceptions import QueryProcessingError

logger = structlog.get_logger(__name__)

# Repeated trailing punctuation (e.g. "???", "!!!", "...") collapsed away.
# Covers ASCII plus common non-Latin terminators (Arabic ؟, Chinese/Japanese
# 。！？, Urdu ۔, fullwidth ．) so multilingual queries normalize symmetrically.
_TRAILING_PUNCT_RE = re.compile(r"[?!.\s\u061F\u06D4\u3002\uFF01\uFF1F\uFF0E]+$")
_WHITESPACE_RE = re.compile(r"\s+")


class QueryPreprocessor:
    """Normalize raw user queries to a canonical form.

    Applies Unicode NFC normalization, lowercasing, whitespace collapsing,
    and trailing punctuation stripping. Non-ASCII characters (e.g. Arabic,
    French, Chinese) are preserved.
    """

    def normalize(self, query: str) -> str:
        """Normalize a raw query string.

        Steps:
            1. Unicode NFC normalization (composes combining characters).
            2. Lowercase.
            3. Collapse internal whitespace to single spaces.
            4. Strip trailing whitespace and repeated punctuation.

        Args:
            query: Raw user input.

        Returns:
            Normalized query string.

        Raises:
            QueryProcessingError: If the normalized query is empty.
        """
        if query is None:
            raise QueryProcessingError("Query is None")

        normalized = unicodedata.normalize("NFC", query)
        normalized = normalized.lower()
        normalized = _WHITESPACE_RE.sub(" ", normalized).strip()
        normalized = _TRAILING_PUNCT_RE.sub("", normalized).strip()

        if not normalized:
            raise QueryProcessingError(
                "Query is empty after normalization",
                detail={"original_query": query},
            )

        logger.debug(
            "query_normalized",
            original_length=len(query),
            normalized_length=len(normalized),
        )
        return normalized
