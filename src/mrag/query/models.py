"""Pydantic models for the query processing module.

Defines the data structures that flow through the query pipeline:
raw query → normalized → contextualized → expanded → ProcessedQuery.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ConversationTurn(BaseModel):
    """A single turn in a multi-turn conversation.

    Attributes:
        query: The user question posed in this turn.
        response: Assistant response text (None if not yet answered).
        timestamp: Unix timestamp of the turn.
    """

    query: str = Field(min_length=1)
    response: str | None = None
    timestamp: float = Field(gt=0.0)


class ExpandedQuery(BaseModel):
    """Result of pseudo-relevance feedback query expansion.

    Attributes:
        original_query: Query text before expansion.
        expanded_query: Query text after appending expansion terms.
        expansion_terms: Terms extracted from PRF documents.
        prf_doc_ids: Doc IDs of the PRF feedback documents.
    """

    original_query: str = Field(min_length=1)
    expanded_query: str = Field(min_length=1)
    expansion_terms: list[str] = Field(default_factory=list)
    prf_doc_ids: list[str] = Field(default_factory=list)


class ProcessedQuery(BaseModel):
    """A query after all preprocessing stages have been applied.

    Attributes:
        original_query: Raw user input before any processing.
        normalized_query: After NFC normalization, lowercasing, whitespace collapse.
        expanded_query: After pseudo-relevance feedback expansion (if enabled).
        final_query: Query string sent to the embedding encoder.
        conversation_history: Recent conversation turns (sliding window).
        query_hash: MD5 hex digest of the normalized query (cache key).
        expansion_terms: Terms added by the expander.
    """

    original_query: str = Field(min_length=1)
    normalized_query: str = Field(min_length=1)
    expanded_query: str | None = None
    final_query: str = Field(min_length=1)
    conversation_history: list[ConversationTurn] = Field(default_factory=list)
    query_hash: str = Field(min_length=32, max_length=32)
    expansion_terms: list[str] = Field(default_factory=list)
