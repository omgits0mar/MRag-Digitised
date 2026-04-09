"""Query expansion via pseudo-relevance feedback (PRF).

Runs an initial retrieval with the raw query, extracts top TF-IDF terms
from the feedback documents, and appends them to the original query to
improve recall on short or ambiguous questions.
"""

from __future__ import annotations

import re

import structlog

from mrag.exceptions import QueryProcessingError
from mrag.query.models import ExpandedQuery
from mrag.retrieval.models import RetrievalRequest

logger = structlog.get_logger(__name__)

_TOKEN_RE = re.compile(r"[^\W\d_]{3,}", flags=re.UNICODE)

# Small, language-agnostic stopword set used only to clean expansion
# candidates; query content itself is unaffected.
_STOPWORDS: frozenset[str] = frozenset(
    {
        "the",
        "and",
        "for",
        "that",
        "this",
        "with",
        "from",
        "have",
        "has",
        "had",
        "are",
        "was",
        "were",
        "not",
        "but",
        "you",
        "your",
        "they",
        "their",
        "them",
        "what",
        "who",
        "when",
        "where",
        "why",
        "how",
        "which",
        "whose",
        "whom",
        "about",
        "into",
        "than",
        "then",
        "there",
        "these",
        "those",
        "been",
        "being",
        "will",
        "would",
        "could",
        "should",
        "may",
        "might",
        "must",
        "any",
        "all",
        "its",
    }
)


class QueryExpander:
    """Expand queries using pseudo-relevance feedback over an existing index.

    Args:
        retriever: A retriever service used to fetch initial PRF documents.
        encoder: Not strictly required here since the retriever owns encoding,
            but kept in the constructor to satisfy the module contract and
            allow future use (e.g. term-embedding re-ranking).
    """

    def __init__(self, retriever, encoder=None) -> None:  # noqa: ANN001
        self._retriever = retriever
        self._encoder = encoder

    def expand(
        self,
        query: str,
        top_n: int = 3,
        max_terms: int = 5,
    ) -> ExpandedQuery:
        """Expand a query with PRF-derived terms.

        Args:
            query: Normalized query string.
            top_n: Number of PRF documents to pull.
            max_terms: Max expansion terms to append.

        Returns:
            ExpandedQuery containing the original and expanded text.

        Raises:
            QueryProcessingError: If PRF retrieval fails catastrophically.
        """
        if not query or not query.strip():
            raise QueryProcessingError("Cannot expand empty query")
        if top_n < 1 or max_terms < 1:
            return ExpandedQuery(
                original_query=query,
                expanded_query=query,
                expansion_terms=[],
                prf_doc_ids=[],
            )

        query_tokens = set(self._tokenize(query))

        try:
            prf_results = self._retriever.retrieve(
                RetrievalRequest(query=query, top_k=top_n)
            )
        except Exception as exc:
            logger.warning(
                "query_expansion_retrieval_failed",
                error=str(exc),
            )
            return ExpandedQuery(
                original_query=query,
                expanded_query=query,
                expansion_terms=[],
                prf_doc_ids=[],
            )

        if not prf_results:
            logger.debug("query_expansion_no_prf_results")
            return ExpandedQuery(
                original_query=query,
                expanded_query=query,
                expansion_terms=[],
                prf_doc_ids=[],
            )

        term_scores: dict[str, float] = {}
        prf_doc_ids: list[str] = []
        for result in prf_results:
            prf_doc_ids.append(result.doc_id)
            weight = float(result.relevance_score) + 1e-6
            for token in self._tokenize(result.chunk_text):
                if token in query_tokens or token in _STOPWORDS:
                    continue
                term_scores[token] = term_scores.get(token, 0.0) + weight

        # Rank expansion candidates by aggregated relevance-weighted frequency.
        ranked_terms = sorted(
            term_scores.items(),
            key=lambda kv: kv[1],
            reverse=True,
        )
        expansion_terms = [term for term, _ in ranked_terms[:max_terms]]

        expanded_text = (
            query if not expansion_terms else f"{query} {' '.join(expansion_terms)}"
        )

        logger.info(
            "query_expanded",
            original_length=len(query),
            expansion_term_count=len(expansion_terms),
            prf_docs=len(prf_doc_ids),
        )

        return ExpandedQuery(
            original_query=query,
            expanded_query=expanded_text,
            expansion_terms=expansion_terms,
            prf_doc_ids=prf_doc_ids,
        )

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        """Simple lowercase word tokenizer that keeps multilingual letters."""
        return [m.group(0).lower() for m in _TOKEN_RE.finditer(text or "")]
