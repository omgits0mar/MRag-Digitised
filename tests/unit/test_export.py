"""Unit tests for JSONL export in mrag.data.export."""

import json
from typing import Any

from mrag.data.models import (
    AnswerType,
    Difficulty,
    DocumentMetadata,
    ProcessedDocument,
    QuestionType,
    TextChunk,
)


def _make_doc(doc_id: str = "d1", question: str = "Q?") -> ProcessedDocument:
    return ProcessedDocument(
        doc_id=doc_id,
        question=question,
        answer_short="Short answer",
        answer_long="A longer answer with more detail.",
        answer_type=AnswerType.BOTH,
        chunks=[
            TextChunk(
                chunk_id=f"{doc_id}_chunk_0",
                doc_id=doc_id,
                text="A longer answer with more detail.",
                start_pos=0,
                end_pos=34,
                token_count=7,
                chunk_index=0,
                total_chunks=1,
            )
        ],
        metadata=DocumentMetadata(
            question_type=QuestionType.FACTOID,
            domain="general",
            difficulty=Difficulty.EASY,
            has_short_answer=True,
            source_id="src_001",
        ),
    )


class TestExportJsonl:
    def test_creates_train_and_eval_files(self, tmp_path: Any) -> None:
        from mrag.data.export import export_jsonl

        docs = [_make_doc(f"d{i}", f"Question {i}?") for i in range(20)]
        train_path, eval_path = export_jsonl(docs, str(tmp_path))
        assert train_path.endswith("train.jsonl")
        assert eval_path.endswith("eval.jsonl")

    def test_jsonl_format(self, tmp_path: Any) -> None:
        from mrag.data.export import export_jsonl

        docs = [_make_doc(f"d{i}", f"Q{i}?") for i in range(10)]
        train_path, eval_path = export_jsonl(docs, str(tmp_path))

        for path in [train_path, eval_path]:
            with open(path, encoding="utf-8") as f:
                for line in f:
                    obj = json.loads(line)
                    assert "doc_id" in obj
                    assert "question" in obj
                    assert "chunks" in obj
                    assert "metadata" in obj

    def test_deterministic_split(self, tmp_path: Any) -> None:
        from mrag.data.export import export_jsonl

        docs = [_make_doc(f"d{i}", f"Q{i}?") for i in range(50)]

        train1, eval1 = export_jsonl(docs, str(tmp_path / "run1"))
        train2, eval2 = export_jsonl(docs, str(tmp_path / "run2"))

        with open(train1, encoding="utf-8") as f1, open(train2, encoding="utf-8") as f2:
            assert f1.read() == f2.read()
        with open(eval1, encoding="utf-8") as f1, open(eval2, encoding="utf-8") as f2:
            assert f1.read() == f2.read()

    def test_approximate_split_ratio(self, tmp_path: Any) -> None:
        from mrag.data.export import export_jsonl

        docs = [_make_doc(f"d{i}", f"Q{i}?") for i in range(100)]
        train_path, eval_path = export_jsonl(docs, str(tmp_path), split_ratio=0.9)

        with open(train_path, encoding="utf-8") as f:
            train_count = sum(1 for _ in f)
        with open(eval_path, encoding="utf-8") as f:
            eval_count = sum(1 for _ in f)

        assert train_count + eval_count == 100
        # Allow 5% tolerance for small datasets
        assert 0.80 <= train_count / 100 <= 1.0

    def test_field_preservation(self, tmp_path: Any) -> None:
        from mrag.data.export import export_jsonl

        doc = _make_doc()
        train_path, _ = export_jsonl([doc], str(tmp_path), split_ratio=1.0)

        with open(train_path, encoding="utf-8") as f:
            obj = json.loads(f.readline())

        assert obj["doc_id"] == "d1"
        assert obj["question"] == "Q?"
        assert obj["answer_type"] == "both"
        assert len(obj["chunks"]) == 1
        assert obj["chunks"][0]["chunk_id"] == "d1_chunk_0"
        assert obj["metadata"]["question_type"] == "factoid"
        assert obj["metadata"]["domain"] == "general"

    def test_custom_split_ratio(self, tmp_path: Any) -> None:
        from mrag.data.export import export_jsonl

        docs = [_make_doc(f"d{i}", f"Q{i}?") for i in range(20)]
        train_path, eval_path = export_jsonl(docs, str(tmp_path), split_ratio=0.5)

        with open(train_path, encoding="utf-8") as f:
            train_count = sum(1 for _ in f)
        with open(eval_path, encoding="utf-8") as f:
            eval_count = sum(1 for _ in f)

        assert train_count + eval_count == 20
