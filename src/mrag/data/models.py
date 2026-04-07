"""Pydantic data models for the MRAG data processing pipeline.

Defines validated schemas for each stage: raw input records, processed
documents, text chunks, document metadata, and pipeline result statistics.
"""

from __future__ import annotations

from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator, model_validator


class AnswerType(str, Enum):
    """Which answer forms are present for a question-answer pair."""

    SHORT = "short"
    LONG = "long"
    BOTH = "both"


class QuestionType(str, Enum):
    """Classified question type based on linguistic patterns."""

    FACTOID = "factoid"
    DESCRIPTIVE = "descriptive"
    LIST = "list"
    YES_NO = "yes_no"
    UNKNOWN = "unknown"


class Difficulty(str, Enum):
    """Difficulty level based on answer availability."""

    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class RawRecord(BaseModel):
    """Raw input from the Natural Questions dataset before processing."""

    question_text: str
    short_answer: str | None = None
    long_answer: str
    document_title: str | None = None
    document_url: str | None = None

    @field_validator("question_text", "long_answer")
    @classmethod
    def must_be_non_empty(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("field must be non-empty after stripping whitespace")
        return stripped

    @field_validator("short_answer")
    @classmethod
    def strip_short_answer(cls, v: str | None) -> str | None:
        if v is not None:
            stripped = v.strip()
            return stripped if stripped else None
        return v


class TextChunk(BaseModel):
    """A segment of text derived from a document, sized for embedding."""

    chunk_id: str
    doc_id: str
    text: str
    start_pos: int = Field(ge=0)
    end_pos: int
    token_count: int = Field(gt=0)
    chunk_index: int = Field(ge=0)
    total_chunks: int = Field(ge=1)

    @field_validator("text")
    @classmethod
    def text_must_be_non_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("chunk text must be non-empty")
        return v

    @model_validator(mode="after")
    def validate_positions_and_indices(self) -> TextChunk:
        if self.end_pos <= self.start_pos:
            raise ValueError("end_pos must be > start_pos")
        if self.chunk_index >= self.total_chunks:
            raise ValueError("chunk_index must be < total_chunks")
        return self


class DocumentMetadata(BaseModel):
    """Enrichment metadata attached to a processed document."""

    question_type: QuestionType
    domain: str = Field(min_length=1)
    difficulty: Difficulty
    has_short_answer: bool
    source_id: str
    language: str = "en"


class ProcessedDocument(BaseModel):
    """A fully processed document ready for embedding."""

    doc_id: str = Field(default_factory=lambda: str(uuid4()))
    question: str
    answer_short: str | None = None
    answer_long: str
    answer_type: AnswerType
    chunks: list[TextChunk] = Field(min_length=1)
    metadata: DocumentMetadata

    @field_validator("question", "answer_long")
    @classmethod
    def must_be_non_empty(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("field must be non-empty")
        return stripped

    @model_validator(mode="after")
    def answer_type_consistency(self) -> ProcessedDocument:
        has_short = self.answer_short is not None and self.answer_short.strip() != ""
        if self.answer_type == AnswerType.SHORT and not has_short:
            raise ValueError("answer_type=short requires answer_short")
        if self.answer_type == AnswerType.LONG and has_short:
            raise ValueError("answer_type=long but answer_short is present")
        return self


class PipelineResult(BaseModel):
    """Statistics from a completed data processing pipeline run."""

    total_records: int = Field(ge=0)
    valid_records: int = Field(ge=0)
    skipped_records: int = Field(ge=0)
    total_chunks: int = Field(ge=0)
    train_count: int = Field(ge=0)
    eval_count: int = Field(ge=0)
    train_file: str | None = None
    eval_file: str | None = None
    elapsed_seconds: float = Field(ge=0.0)
