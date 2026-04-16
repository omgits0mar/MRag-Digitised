"""Unit tests for API Pydantic schemas and middleware."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from mrag.api.schemas import (
    AnalyticsResponse,
    ErrorEnvelope,
    EvaluateRequest,
    HealthResponse,
    QuestionRequest,
    QuestionResponse,
    SourceResponse,
)


class TestQuestionRequest:
    def test_valid_payload(self):
        req = QuestionRequest(question="What is photosynthesis?")
        assert req.question == "What is photosynthesis?"
        assert req.expand is True
        assert req.conversation_id is None

    def test_with_all_fields(self):
        req = QuestionRequest(
            question="What is DNA?",
            conversation_id="conv-001",
            expand=False,
            temperature=0.5,
            max_tokens=2048,
        )
        assert req.conversation_id == "conv-001"
        assert req.temperature == 0.5

    def test_empty_question_rejected(self):
        with pytest.raises(ValidationError):
            QuestionRequest(question="")

    def test_too_long_question_rejected(self):
        with pytest.raises(ValidationError):
            QuestionRequest(question="x" * 2001)

    def test_temperature_out_of_range(self):
        with pytest.raises(ValidationError):
            QuestionRequest(question="test", temperature=3.0)

    def test_max_tokens_out_of_range(self):
        with pytest.raises(ValidationError):
            QuestionRequest(question="test", max_tokens=0)


class TestQuestionResponse:
    def test_valid_response(self):
        resp = QuestionResponse(
            answer="DNA is a molecule.",
            confidence_score=0.85,
            is_fallback=False,
            sources=[],
            response_time_ms=1500.0,
        )
        assert resp.answer == "DNA is a molecule."
        assert resp.response_time_ms == 1500.0

    def test_confidence_out_of_range(self):
        with pytest.raises(ValidationError):
            QuestionResponse(
                answer="test",
                confidence_score=1.5,
                is_fallback=False,
                sources=[],
                response_time_ms=100.0,
            )


class TestSourceResponse:
    def test_valid_source(self):
        src = SourceResponse(
            chunk_id="c_001",
            doc_id="d_001",
            text="Some text",
            relevance_score=0.9,
        )
        assert src.relevance_score == 0.9


class TestHealthResponse:
    def test_healthy(self):
        resp = HealthResponse(
            status="healthy",
            vector_store="loaded",
            llm_provider="reachable",
            database="connected",
            uptime_seconds=3600.0,
            persistence_failure_count=0,
        )
        assert resp.status == "healthy"


class TestErrorEnvelope:
    def test_valid_error(self):
        err = ErrorEnvelope(
            error="validation_error",
            detail="field required",
            status_code=422,
        )
        assert err.status_code == 422


class TestEvaluateRequest:
    def test_defaults(self):
        req = EvaluateRequest()
        assert req.dataset_path is None
        assert req.generate_report is True
        assert req.compare_baseline is True


class TestAnalyticsResponse:
    def test_valid_response(self):
        resp = AnalyticsResponse(
            total_queries=100,
            avg_latency_ms=1500.0,
            cache_hit_rate=0.35,
        )
        assert resp.total_queries == 100
