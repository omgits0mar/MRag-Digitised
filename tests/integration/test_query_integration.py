"""Integration test: full query pipeline end-to-end (real preprocessor, mocked PRF)."""

from __future__ import annotations

import hashlib
from unittest.mock import MagicMock

from mrag.query.context_manager import ConversationContextManager
from mrag.query.expander import QueryExpander
from mrag.query.models import ExpandedQuery
from mrag.query.pipeline import QueryPipeline
from mrag.query.preprocessor import QueryPreprocessor


class TestQueryPipelineIntegration:
    def test_raw_input_to_processed_query(self) -> None:
        """'  What  IS   Photosynthesis?? ' normalizes and expands."""
        pre = QueryPreprocessor()

        expander = MagicMock(spec=QueryExpander)
        expander.expand.return_value = ExpandedQuery(
            original_query="what is photosynthesis",
            expanded_query="what is photosynthesis chlorophyll light",
            expansion_terms=["chlorophyll", "light"],
            prf_doc_ids=["doc_1"],
        )

        pipeline = QueryPipeline(preprocessor=pre, expander=expander)
        result = pipeline.process("  What  IS   Photosynthesis?? ")

        assert result.normalized_query == "what is photosynthesis"
        assert result.expanded_query == "what is photosynthesis chlorophyll light"
        assert result.final_query == "what is photosynthesis chlorophyll light"
        expected_hash = hashlib.md5(
            b"what is photosynthesis"
        ).hexdigest()
        assert result.query_hash == expected_hash
        assert result.expansion_terms == ["chlorophyll", "light"]

    def test_multilingual_normalization(self) -> None:
        pre = QueryPreprocessor()
        pipeline = QueryPipeline(preprocessor=pre, expander=None)
        result = pipeline.process("  Qu'est-ce que l'Énergie ? ")
        assert "énergie" in result.normalized_query
        assert (
            result.query_hash
            == hashlib.md5(result.normalized_query.encode("utf-8")).hexdigest()
        )

    def test_contextualized_multi_turn(self) -> None:
        pre = QueryPreprocessor()
        ctx = ConversationContextManager(max_turns=3)
        ctx.add_turn("what is DNA", "deoxyribonucleic acid")
        ctx.add_turn("what does it encode", "genetic information")

        pipeline = QueryPipeline(preprocessor=pre, expander=None, context_manager=ctx)
        result = pipeline.process("how is it replicated")

        assert "Previous Q: what is DNA" in result.final_query
        assert "Previous Q: what does it encode" in result.final_query
        assert "Current Q: how is it replicated" in result.final_query
        assert len(result.conversation_history) == 2

    def test_no_expansion_returns_clean_pipeline(self) -> None:
        pre = QueryPreprocessor()
        pipeline = QueryPipeline(preprocessor=pre, expander=None)
        result = pipeline.process("simple query", expand=False)
        assert result.expanded_query is None
        assert result.final_query == "simple query"
