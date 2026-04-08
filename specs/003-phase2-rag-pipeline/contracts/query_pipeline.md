# Contract: Query Pipeline

**Module**: `src/mrag/query/`

## QueryPreprocessor

```python
class QueryPreprocessor:
    def normalize(self, query: str) -> str:
        """Normalize a raw query string.

        - Unicode NFC normalization
        - Lowercase
        - Collapse whitespace
        - Strip excessive punctuation (trailing repeated ?!.)

        Args:
            query: Raw user input.

        Returns:
            Normalized query string.

        Raises:
            QueryProcessingError: If query is empty after normalization.
        """
```

## QueryExpander

```python
class QueryExpander:
    def __init__(self, retriever: RetrieverService, encoder: EmbeddingEncoder) -> None: ...

    def expand(
        self,
        query: str,
        top_n: int = 3,
        max_terms: int = 5,
    ) -> ExpandedQuery:
        """Expand a query via pseudo-relevance feedback.

        1. Retrieve top_n documents using the raw query
        2. Extract top max_terms TF-IDF terms from retrieved docs
        3. Append terms to original query

        Args:
            query: Normalized query string.
            top_n: Number of PRF documents.
            max_terms: Max expansion terms.

        Returns:
            ExpandedQuery with original, expanded text, and terms.
        """
```

## ConversationContextManager

```python
class ConversationContextManager:
    def __init__(self, max_turns: int = 5) -> None: ...

    def add_turn(self, query: str, response: str | None = None) -> None:
        """Record a conversation turn."""

    def get_contextualized_query(self, current_query: str) -> str:
        """Prepend recent history to current query for context.

        Returns:
            Query string with history context prepended.
        """

    def clear(self) -> None:
        """Reset conversation history."""
```

## QueryPipeline

```python
class QueryPipeline:
    def __init__(
        self,
        preprocessor: QueryPreprocessor,
        expander: QueryExpander | None,
        context_manager: ConversationContextManager | None,
    ) -> None: ...

    def process(
        self,
        query: str,
        expand: bool = True,
    ) -> ProcessedQuery:
        """Run full query processing pipeline.

        1. Normalize
        2. Contextualize (if context_manager provided)
        3. Expand (if expander provided and expand=True)
        4. Compute query hash

        Returns:
            ProcessedQuery with all processing stages applied.
        """
```
