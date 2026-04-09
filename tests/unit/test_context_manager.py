"""Unit tests for mrag.query.context_manager.ConversationContextManager."""

from __future__ import annotations

import pytest

from mrag.query.context_manager import ConversationContextManager


class TestConversationContextManager:
    def test_empty_history_returns_query_unchanged(self) -> None:
        ctx = ConversationContextManager()
        assert ctx.get_contextualized_query("what is DNA") == "what is DNA"

    def test_single_turn_prepends_previous_query(self) -> None:
        ctx = ConversationContextManager()
        ctx.add_turn("what is DNA", "DNA is deoxyribonucleic acid")
        out = ctx.get_contextualized_query("what does it encode")
        assert "Previous Q: what is DNA" in out
        assert "A: DNA is deoxyribonucleic acid" in out
        assert "Current Q: what does it encode" in out

    def test_add_turn_without_response(self) -> None:
        ctx = ConversationContextManager()
        ctx.add_turn("what is DNA")
        out = ctx.get_contextualized_query("explain more")
        assert "Previous Q: what is DNA" in out
        # No "A:" line for a turn without a response.
        assert "A:" not in out

    def test_max_turns_sliding_window(self) -> None:
        ctx = ConversationContextManager(max_turns=3)
        for i in range(5):
            ctx.add_turn(f"q{i}", f"a{i}")
        history = ctx.history
        assert len(history) == 3
        assert [t.query for t in history] == ["q2", "q3", "q4"]

    def test_clear_resets_history(self) -> None:
        ctx = ConversationContextManager()
        ctx.add_turn("q1", "a1")
        ctx.clear()
        assert ctx.history == []
        assert ctx.get_contextualized_query("new") == "new"

    def test_invalid_max_turns_raises(self) -> None:
        with pytest.raises(ValueError):
            ConversationContextManager(max_turns=0)
