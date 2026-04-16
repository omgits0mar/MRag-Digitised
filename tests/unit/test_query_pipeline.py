"""Unit tests for mrag.query.pipeline.QueryPipeline end-to-end chaining."""

from __future__ import annotations

import hashlib
from unittest.mock import MagicMock

from mrag.query.context_manager import ConversationContextManager
from mrag.query.expander import QueryExpander
from mrag.query.models import ExpandedQuery
from mrag.query.pipeline import QueryPipeline
from mrag.query.preprocessor import QueryPreprocessor


class TestQueryPipeline:
    def test_end_to_end_chain(self) -> None:
        pre = QueryPreprocessor()

        expander = MagicMock(spec=QueryExpander)
        expander.expand.return_value = ExpandedQuery(
            original_query="what is photosynthesis",
            expanded_query="what is photosynthesis chlorophyll light",
            expansion_terms=["chlorophyll", "light"],
            prf_doc_ids=["doc1"],
        )

        ctx = ConversationContextManager()

        pipeline = QueryPipeline(
            preprocessor=pre,
            expander=expander,
            context_manager=ctx,
        )

        result = pipeline.process("  What  IS   Photosynthesis?? ")
        assert result.normalized_query == "what is photosynthesis"
        assert result.expanded_query == "what is photosynthesis chlorophyll light"
        assert result.expansion_terms == ["chlorophyll", "light"]
        assert result.final_query == "what is photosynthesis chlorophyll light"
        expected_hash = hashlib.md5(
            b"what is photosynthesis"
        ).hexdigest()
        assert result.query_hash == expected_hash

    def test_expansion_disabled_via_flag(self) -> None:
        pre = QueryPreprocessor()
        expander = MagicMock(spec=QueryExpander)
        pipeline = QueryPipeline(preprocessor=pre, expander=expander)
        result = pipeline.process("what is DNA", expand=False)
        expander.expand.assert_not_called()
        assert result.expanded_query is None
        assert result.final_query == "what is dna"

    def test_no_expander(self) -> None:
        pre = QueryPreprocessor()
        pipeline = QueryPipeline(preprocessor=pre, expander=None)
        result = pipeline.process("what is DNA")
        assert result.expanded_query is None
        assert result.final_query == "what is dna"

    def test_no_context_manager(self) -> None:
        pre = QueryPreprocessor()
        pipeline = QueryPipeline(preprocessor=pre)
        result = pipeline.process("test query")
        assert result.conversation_history == []
        assert result.final_query == "test query"

    def test_history_is_included_in_final_query(self) -> None:
        pre = QueryPreprocessor()
        ctx = ConversationContextManager()
        ctx.add_turn("what is dna", "deoxyribonucleic acid")

        pipeline = QueryPipeline(
            preprocessor=pre,
            expander=None,
            context_manager=ctx,
        )
        result = pipeline.process("what does it encode")
        assert "Previous Q: what is dna" in result.final_query
        assert "Current Q: what does it encode" in result.final_query
        assert len(result.conversation_history) == 1
