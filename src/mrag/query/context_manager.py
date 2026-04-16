"""Conversation context manager for multi-turn queries.

Maintains a sliding window of recent turns and exposes a heuristic
"history prepend" method that decorates the current query with prior
context without an extra LLM call.
"""

from __future__ import annotations

import time
from collections import deque

import structlog

from mrag.query.models import ConversationTurn

logger = structlog.get_logger(__name__)


class ConversationContextManager:
    """Track the recent history of a conversation for contextual resolution.

    Args:
        max_turns: Maximum number of turns retained in the sliding window.
    """

    def __init__(self, max_turns: int = 5) -> None:
        if max_turns < 1:
            raise ValueError("max_turns must be >= 1")
        self._max_turns = max_turns
        self._history: deque[ConversationTurn] = deque(maxlen=max_turns)

    def add_turn(self, query: str, response: str | None = None) -> None:
        """Append a turn to the conversation history.

        Oldest turn is evicted once ``max_turns`` is exceeded.

        Args:
            query: The user query for this turn.
            response: Optional assistant response for this turn.
        """
        turn = ConversationTurn(
            query=query,
            response=response,
            timestamp=time.time(),
        )
        self._history.append(turn)
        logger.debug(
            "context_turn_added",
            history_size=len(self._history),
            max_turns=self._max_turns,
        )

    def get_contextualized_query(self, current_query: str) -> str:
        """Prepend recent history as context to the current query.

        If no history exists, returns the current query unchanged. Otherwise
        produces a heuristic "Previous Q: ... A: ..." preamble followed by
        the current query.

        Args:
            current_query: The query to contextualize.

        Returns:
            Query string with context prepended.
        """
        if not self._history:
            return current_query

        lines: list[str] = []
        for turn in self._history:
            lines.append(f"Previous Q: {turn.query}")
            if turn.response:
                lines.append(f"A: {turn.response}")
        lines.append(f"Current Q: {current_query}")
        contextualized = "\n".join(lines)

        logger.debug(
            "query_contextualized",
            turns_prepended=len(self._history),
            contextualized_length=len(contextualized),
        )
        return contextualized

    def clear(self) -> None:
        """Reset all conversation history."""
        self._history.clear()
        logger.debug("context_cleared")

    @property
    def history(self) -> list[ConversationTurn]:
        """Return a copy of the recent history."""
        return list(self._history)

    @property
    def max_turns(self) -> int:
        """Maximum number of turns retained."""
        return self._max_turns
