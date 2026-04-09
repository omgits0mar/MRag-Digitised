"""Unit tests for mrag.generation.prompt_builder.PromptBuilder."""

from __future__ import annotations

import os
import time
from pathlib import Path

import pytest

from mrag.exceptions import ResponseGenerationError
from mrag.generation.prompt_builder import PromptBuilder
from mrag.query.models import ConversationTurn
from mrag.retrieval.models import RetrievalResult


def _chunk(text: str, score: float = 0.8, idx: int = 0) -> RetrievalResult:
    return RetrievalResult(
        chunk_id=f"c{idx}",
        doc_id=f"d{idx}",
        chunk_text=text,
        relevance_score=score,
        cosine_similarity=score,
        question="q",
        answer_short="short",
        answer_long=text,
        question_type="factoid",
        domain="science",
        difficulty="easy",
        has_short_answer=True,
    )


def _make_templates(tmp_path: Path) -> Path:
    templates = tmp_path / "templates"
    templates.mkdir()
    (templates / "qa_prompt.j2").write_text(
        "Q: {{ query }}\n"
        "{% for c in context_chunks %}[{{ loop.index }}] {{ c.chunk_text }}\n"
        "{% endfor %}"
        "{% for t in conversation_history %}H: {{ t.query }}\n{% endfor %}",
        encoding="utf-8",
    )
    (templates / "system_prompt.j2").write_text(
        "You are a test assistant.", encoding="utf-8"
    )
    (templates / "fallback_prompt.j2").write_text(
        "No answer for: {{ query }}", encoding="utf-8"
    )
    return templates


class TestPromptBuilder:
    def test_build_qa_prompt_injects_context(self, tmp_path: Path) -> None:
        templates = _make_templates(tmp_path)
        pb = PromptBuilder(templates_dir=str(templates))
        out = pb.build_qa_prompt(
            query="what is DNA",
            context_chunks=[
                _chunk("DNA is a molecule", 0.9, 1),
                _chunk("DNA carries genetic information", 0.8, 2),
            ],
        )
        assert "Q: what is DNA" in out
        assert "[1] DNA is a molecule" in out
        assert "[2] DNA carries genetic information" in out

    def test_build_qa_prompt_includes_history(self, tmp_path: Path) -> None:
        templates = _make_templates(tmp_path)
        pb = PromptBuilder(templates_dir=str(templates))
        history = [
            ConversationTurn(query="q1", response="a1", timestamp=time.time()),
        ]
        out = pb.build_qa_prompt(
            query="follow up",
            context_chunks=[_chunk("context")],
            conversation_history=history,
        )
        assert "H: q1" in out

    def test_build_system_prompt(self, tmp_path: Path) -> None:
        templates = _make_templates(tmp_path)
        pb = PromptBuilder(templates_dir=str(templates))
        assert "test assistant" in pb.build_system_prompt()

    def test_fallback_prompt_interpolates_query(self, tmp_path: Path) -> None:
        templates = _make_templates(tmp_path)
        pb = PromptBuilder(templates_dir=str(templates))
        out = pb.build_fallback_prompt("unanswerable thing")
        assert "No answer for: unanswerable thing" in out

    def test_missing_template_raises(self, tmp_path: Path) -> None:
        pb = PromptBuilder(templates_dir=str(tmp_path / "does_not_exist"))
        with pytest.raises(ResponseGenerationError):
            pb.build_system_prompt()

    def test_hot_reload_on_mtime_change(self, tmp_path: Path) -> None:
        templates = _make_templates(tmp_path)
        pb = PromptBuilder(templates_dir=str(templates))
        first = pb.build_system_prompt()
        assert "test assistant" in first

        # Overwrite and bump mtime beyond the cached value.
        sys_path = templates / "system_prompt.j2"
        sys_path.write_text("Updated system prompt.", encoding="utf-8")
        new_mtime = os.path.getmtime(sys_path) + 1
        os.utime(sys_path, (new_mtime, new_mtime))

        second = pb.build_system_prompt()
        assert second == "Updated system prompt."
