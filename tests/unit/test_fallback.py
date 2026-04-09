"""Unit tests for mrag.generation.fallback.FallbackHandler."""

from __future__ import annotations

from pathlib import Path

from mrag.generation.fallback import FallbackHandler
from mrag.generation.prompt_builder import PromptBuilder


def _templates(tmp_path: Path) -> Path:
    t = tmp_path / "t"
    t.mkdir()
    (t / "qa_prompt.j2").write_text("ignored", encoding="utf-8")
    (t / "system_prompt.j2").write_text("ignored", encoding="utf-8")
    (t / "fallback_prompt.j2").write_text(
        "I cannot answer: {{ query }}", encoding="utf-8"
    )
    return t


class TestFallbackHandler:
    def test_get_fallback_returns_non_empty(self, tmp_path: Path) -> None:
        t = _templates(tmp_path)
        handler = FallbackHandler(PromptBuilder(templates_dir=str(t)))
        result = handler.get_fallback_response("some question")
        assert result
        assert "some question" in result

    def test_real_fallback_template_renders(self) -> None:
        handler = FallbackHandler(PromptBuilder(templates_dir="prompts/templates"))
        result = handler.get_fallback_response("what is x")
        assert len(result) > 0
        assert "what is x" in result
