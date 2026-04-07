"""Unit tests for data models in mrag.data.models."""

import pytest
from pydantic import ValidationError

from mrag.data.models import (
    AnswerType,
    Difficulty,
    DocumentMetadata,
    PipelineResult,
    ProcessedDocument,
    QuestionType,
    RawRecord,
    TextChunk,
)

# ---------------------------------------------------------------------------
# RawRecord
# ---------------------------------------------------------------------------


class TestRawRecord:
    def test_valid_record(self) -> None:
        r = RawRecord(
            question_text="Who is Einstein?",
            short_answer="A physicist",
            long_answer="Albert Einstein was a theoretical physicist.",
            document_title="Einstein",
            document_url="https://example.com",
        )
        assert r.question_text == "Who is Einstein?"
        assert r.short_answer == "A physicist"

    def test_valid_without_optional_fields(self) -> None:
        r = RawRecord(
            question_text="What is X?",
            long_answer="X is something.",
        )
        assert r.short_answer is None
        assert r.document_title is None
        assert r.document_url is None

    def test_empty_question_raises(self) -> None:
        with pytest.raises(ValidationError):
            RawRecord(question_text="", long_answer="some answer")

    def test_whitespace_only_question_raises(self) -> None:
        with pytest.raises(ValidationError):
            RawRecord(question_text="   ", long_answer="some answer")

    def test_empty_long_answer_raises(self) -> None:
        with pytest.raises(ValidationError):
            RawRecord(question_text="What is X?", long_answer="")

    def test_whitespace_stripped(self) -> None:
        r = RawRecord(
            question_text="  What is X?  ",
            long_answer="  X is something.  ",
        )
        assert r.question_text == "What is X?"
        assert r.long_answer == "X is something."

    def test_short_answer_none_preserved(self) -> None:
        r = RawRecord(
            question_text="Q?",
            long_answer="A.",
            short_answer=None,
        )
        assert r.short_answer is None

    def test_short_answer_whitespace_becomes_none(self) -> None:
        r = RawRecord(
            question_text="Q?",
            long_answer="A.",
            short_answer="   ",
        )
        assert r.short_answer is None


# ---------------------------------------------------------------------------
# TextChunk
# ---------------------------------------------------------------------------


class TestTextChunk:
    def _make_chunk(self, **overrides: object) -> TextChunk:
        defaults = {
            "chunk_id": "doc1_chunk_0",
            "doc_id": "doc1",
            "text": "Some text content here.",
            "start_pos": 0,
            "end_pos": 23,
            "token_count": 5,
            "chunk_index": 0,
            "total_chunks": 1,
        }
        defaults.update(overrides)
        return TextChunk(**defaults)  # type: ignore[arg-type]

    def test_valid_chunk(self) -> None:
        chunk = self._make_chunk()
        assert chunk.chunk_id == "doc1_chunk_0"
        assert chunk.token_count == 5

    def test_end_pos_must_exceed_start(self) -> None:
        with pytest.raises(ValidationError):
            self._make_chunk(start_pos=10, end_pos=10)

    def test_end_pos_less_than_start_raises(self) -> None:
        with pytest.raises(ValidationError):
            self._make_chunk(start_pos=20, end_pos=10)

    def test_empty_text_raises(self) -> None:
        with pytest.raises(ValidationError):
            self._make_chunk(text="   ")

    def test_chunk_index_equals_total_raises(self) -> None:
        with pytest.raises(ValidationError):
            self._make_chunk(chunk_index=1, total_chunks=1)

    def test_negative_start_pos_raises(self) -> None:
        with pytest.raises(ValidationError):
            self._make_chunk(start_pos=-1)

    def test_zero_token_count_raises(self) -> None:
        with pytest.raises(ValidationError):
            self._make_chunk(token_count=0)

    def test_zero_total_chunks_raises(self) -> None:
        with pytest.raises(ValidationError):
            self._make_chunk(total_chunks=0)


# ---------------------------------------------------------------------------
# DocumentMetadata
# ---------------------------------------------------------------------------


class TestDocumentMetadata:
    def test_valid_metadata(self) -> None:
        m = DocumentMetadata(
            question_type=QuestionType.FACTOID,
            domain="science",
            difficulty=Difficulty.EASY,
            has_short_answer=True,
            source_id="src_001",
            language="en",
        )
        assert m.question_type == QuestionType.FACTOID
        assert m.domain == "science"

    def test_empty_domain_raises(self) -> None:
        with pytest.raises(ValidationError):
            DocumentMetadata(
                question_type=QuestionType.UNKNOWN,
                domain="",
                difficulty=Difficulty.MEDIUM,
                has_short_answer=False,
                source_id="src_002",
            )

    def test_default_language(self) -> None:
        m = DocumentMetadata(
            question_type=QuestionType.FACTOID,
            domain="history",
            difficulty=Difficulty.HARD,
            has_short_answer=False,
            source_id="src_003",
        )
        assert m.language == "en"


# ---------------------------------------------------------------------------
# ProcessedDocument
# ---------------------------------------------------------------------------


class TestProcessedDocument:
    def _make_doc(self, **overrides: object) -> ProcessedDocument:
        chunk = TextChunk(
            chunk_id="d1_chunk_0",
            doc_id="d1",
            text="Some content.",
            start_pos=0,
            end_pos=13,
            token_count=2,
            chunk_index=0,
            total_chunks=1,
        )
        meta = DocumentMetadata(
            question_type=QuestionType.FACTOID,
            domain="science",
            difficulty=Difficulty.EASY,
            has_short_answer=True,
            source_id="src_001",
        )
        defaults = {
            "doc_id": "d1",
            "question": "What is X?",
            "answer_short": "X is Y",
            "answer_long": "X is Y because of Z.",
            "answer_type": AnswerType.BOTH,
            "chunks": [chunk],
            "metadata": meta,
        }
        defaults.update(overrides)
        return ProcessedDocument(**defaults)  # type: ignore[arg-type]

    def test_valid_document(self) -> None:
        doc = self._make_doc()
        assert doc.question == "What is X?"
        assert len(doc.chunks) == 1

    def test_auto_generated_doc_id(self) -> None:
        doc = self._make_doc()
        del doc  # just checking constructor works without doc_id
        doc2 = ProcessedDocument(
            question="Q?",
            answer_long="A.",
            answer_type=AnswerType.LONG,
            chunks=[
                TextChunk(
                    chunk_id="c1",
                    doc_id="auto",
                    text="A.",
                    start_pos=0,
                    end_pos=2,
                    token_count=1,
                    chunk_index=0,
                    total_chunks=1,
                )
            ],
            metadata=DocumentMetadata(
                question_type=QuestionType.UNKNOWN,
                domain="general",
                difficulty=Difficulty.MEDIUM,
                has_short_answer=False,
                source_id="src",
            ),
        )
        assert len(doc2.doc_id) > 0

    def test_answer_type_short_without_short_answer_raises(self) -> None:
        with pytest.raises(ValidationError):
            self._make_doc(answer_type=AnswerType.SHORT, answer_short=None)

    def test_answer_type_long_with_short_answer_raises(self) -> None:
        with pytest.raises(ValidationError):
            self._make_doc(answer_type=AnswerType.LONG, answer_short="present")

    def test_empty_chunks_raises(self) -> None:
        with pytest.raises(ValidationError):
            self._make_doc(chunks=[])

    def test_empty_question_raises(self) -> None:
        with pytest.raises(ValidationError):
            self._make_doc(question="   ")


# ---------------------------------------------------------------------------
# PipelineResult
# ---------------------------------------------------------------------------


class TestPipelineResult:
    def test_valid_result(self) -> None:
        r = PipelineResult(
            total_records=100,
            valid_records=95,
            skipped_records=5,
            total_chunks=300,
            train_count=85,
            eval_count=10,
            train_file="/data/train.jsonl",
            eval_file="/data/eval.jsonl",
            elapsed_seconds=12.5,
        )
        assert r.total_records == 100
        assert r.train_count == 85

    def test_negative_counts_raise(self) -> None:
        with pytest.raises(ValidationError):
            PipelineResult(
                total_records=-1,
                valid_records=0,
                skipped_records=0,
                total_chunks=0,
                train_count=0,
                eval_count=0,
                elapsed_seconds=0.0,
            )
