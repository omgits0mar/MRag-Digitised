"""Fallback response handler for low-confidence / empty-context cases.

Renders the ``fallback_prompt.j2`` template via ``PromptBuilder`` so that
the fallback text is externalized and reuses the same hot-reload cache as
the production prompts.
"""

from __future__ import annotations

import structlog

from mrag.generation.prompt_builder import PromptBuilder

logger = structlog.get_logger(__name__)


class FallbackHandler:
    """Produce canned responses when the system cannot answer confidently.

    Args:
        prompt_builder: PromptBuilder used to render the fallback template.
    """

    def __init__(self, prompt_builder: PromptBuilder) -> None:
        self._prompt_builder = prompt_builder

    def get_fallback_response(self, query: str) -> str:
        """Return the rendered fallback message for ``query``."""
        text = self._prompt_builder.build_fallback_prompt(query)
        logger.info("fallback_response_generated", query_length=len(query or ""))
        return text
