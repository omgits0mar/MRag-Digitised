"""Jinja2 prompt builder with mtime-based hot reloading.

Templates live under ``prompts/templates/``. Each template is cached
alongside its file modification time so that edits on disk are picked up
on the next call without restarting the process.
"""

from __future__ import annotations

import os

import structlog
from jinja2 import Environment, FileSystemLoader, StrictUndefined, Template

from mrag.exceptions import ResponseGenerationError
from mrag.query.models import ConversationTurn
from mrag.retrieval.models import RetrievalResult

logger = structlog.get_logger(__name__)

_QA_TEMPLATE = "qa_prompt.j2"
_SYSTEM_TEMPLATE = "system_prompt.j2"
_FALLBACK_TEMPLATE = "fallback_prompt.j2"


class PromptBuilder:
    """Load and render Jinja2 prompt templates with mtime hot-reload.

    Args:
        templates_dir: Directory containing the Jinja2 templates.
    """

    def __init__(self, templates_dir: str = "prompts/templates") -> None:
        self._templates_dir = templates_dir
        self._env = Environment(
            loader=FileSystemLoader(templates_dir),
            autoescape=False,  # Plain-text prompts, not HTML.
            undefined=StrictUndefined,
            trim_blocks=True,
            lstrip_blocks=True,
        )
        # Each entry: name -> (mtime, compiled Template).
        self._cache: dict[str, tuple[float, Template]] = {}

    # ------------------------------------------------------------------ helpers

    def _template_path(self, name: str) -> str:
        return os.path.join(self._templates_dir, name)

    def _load(self, name: str) -> Template:
        """Return a compiled template, re-compiling when its mtime changes."""
        path = self._template_path(name)
        try:
            mtime = os.path.getmtime(path)
        except OSError as exc:
            raise ResponseGenerationError(
                f"Prompt template not found: {name}",
                detail={"path": path, "error": str(exc)},
            ) from exc

        cached = self._cache.get(name)
        if cached is not None and cached[0] == mtime:
            return cached[1]

        try:
            template = self._env.get_template(name)
        except Exception as exc:  # noqa: BLE001 — jinja2 errors are diverse
            raise ResponseGenerationError(
                f"Failed to load prompt template: {name}",
                detail={"path": path, "error": str(exc)},
            ) from exc

        self._cache[name] = (mtime, template)
        logger.debug("prompt_template_loaded", name=name, mtime=mtime)
        return template

    # ----------------------------------------------------------------- public API

    def build_qa_prompt(
        self,
        query: str,
        context_chunks: list[RetrievalResult],
        conversation_history: list[ConversationTurn] | None = None,
    ) -> str:
        """Render the Q&A prompt template with the provided context.

        Args:
            query: The normalized / contextualized user query.
            context_chunks: Retrieved passages to inject as numbered context.
            conversation_history: Optional prior turns for multi-turn prompts.

        Returns:
            Rendered prompt string.
        """
        template = self._load(_QA_TEMPLATE)
        try:
            rendered = template.render(
                query=query,
                context_chunks=[c.model_dump() for c in context_chunks],
                conversation_history=[
                    t.model_dump() for t in (conversation_history or [])
                ],
            )
        except Exception as exc:  # noqa: BLE001
            raise ResponseGenerationError(
                "Failed to render QA prompt",
                detail={"error": str(exc)},
            ) from exc
        logger.debug(
            "qa_prompt_built",
            query_length=len(query),
            context_chunks=len(context_chunks),
            history_turns=len(conversation_history or []),
            prompt_length=len(rendered),
        )
        return rendered

    def build_system_prompt(self) -> str:
        """Render the system instruction template."""
        template = self._load(_SYSTEM_TEMPLATE)
        try:
            return template.render()
        except Exception as exc:  # noqa: BLE001
            raise ResponseGenerationError(
                "Failed to render system prompt",
                detail={"error": str(exc)},
            ) from exc

    def build_fallback_prompt(self, query: str) -> str:
        """Render the fallback response template."""
        template = self._load(_FALLBACK_TEMPLATE)
        try:
            return template.render(query=query)
        except Exception as exc:  # noqa: BLE001
            raise ResponseGenerationError(
                "Failed to render fallback prompt",
                detail={"error": str(exc)},
            ) from exc
