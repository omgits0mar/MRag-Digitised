"""Query processing pipeline orchestrator.

Chains preprocessor → context manager → expander to produce a
ProcessedQuery with an MD5 hash ready for cache lookup.
"""

from __future__ import annotations

import hashlib

import structlog

from mrag.query.context_manager import ConversationContextManager
from mrag.query.expander import QueryExpander
from mrag.query.models import ProcessedQuery
from mrag.query.preprocessor import QueryPreprocessor

logger = structlog.get_logger(__name__)


class QueryPipeline:
    """End-to-end query processing pipeline.

    Args:
        preprocessor: Required normalizer.
        expander: Optional PRF expander; skipped when None or when
            ``process(..., expand=False)``.
        context_manager: Optional multi-turn context manager; when absent
            the query is not contextualized (single-turn mode).
    """

    def __init__(
        self,
        preprocessor: QueryPreprocessor,
        expander: QueryExpander | None = None,
        context_manager: ConversationContextManager | None = None,
    ) -> None:
        self._preprocessor = preprocessor
        self._expander = expander
        self._context_manager = context_manager

    def process(self, query: str, expand: bool = True) -> ProcessedQuery:
        """Run the full query-processing pipeline.

        Stages:
            1. Normalize (``QueryPreprocessor``).
            2. Contextualize, if a context manager is attached. The
               contextualized form is used only as the LLM-facing
               ``final_query``; the normalized form remains the cache key.
            3. Expand via PRF, if enabled and an expander is attached.
            4. Compute the MD5 hash of the normalized query.

        Args:
            query: Raw user query.
            expand: Whether to run PRF expansion.

        Returns:
            A fully populated ``ProcessedQuery``.
        """
        logger.debug("query_pipeline_start", raw_length=len(query or ""))

        normalized = self._preprocessor.normalize(query)

        expanded_text: str | None = None
        expansion_terms: list[str] = []
        if expand and self._expander is not None:
            expanded = self._expander.expand(normalized)
            expanded_text = expanded.expanded_query
            expansion_terms = list(expanded.expansion_terms)

        # Base query used for retrieval (expanded form if available).
        retrieval_query = expanded_text if expanded_text else normalized

        if self._context_manager is not None:
            final_query = self._context_manager.get_contextualized_query(
                retrieval_query
            )
            history = self._context_manager.history
        else:
            final_query = retrieval_query
            history = []

        query_hash = hashlib.md5(normalized.encode("utf-8")).hexdigest()

        logger.info(
            "query_pipeline_complete",
            expansion_terms=len(expansion_terms),
            history_turns=len(history),
            query_hash=query_hash,
        )

        return ProcessedQuery(
            original_query=query,
            normalized_query=normalized,
            expanded_query=expanded_text,
            final_query=final_query,
            conversation_history=history,
            query_hash=query_hash,
            expansion_terms=expansion_terms,
        )
