"""Global error handler and middleware for the MRAG API.

Maps unhandled exceptions to the Constitution-mandated ErrorEnvelope
format: ``{"error": str, "detail": str, "status_code": int}``.
"""

from __future__ import annotations

import time

import structlog
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from mrag.api.schemas import ErrorEnvelope
from mrag.exceptions import DatabaseError, EvaluationError

logger = structlog.get_logger(__name__)


async def global_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch all unhandled exceptions and return ErrorEnvelope JSON.

    Maps:
        RequestValidationError -> 422
        DatabaseError          -> 500
        EvaluationError        -> 500
        Exception              -> 500
    """
    if isinstance(exc, RequestValidationError):
        envelope = ErrorEnvelope(
            error="validation_error",
            detail=str(exc),
            status_code=422,
        )
        return JSONResponse(status_code=422, content=envelope.model_dump())

    if isinstance(exc, DatabaseError):
        logger.error("database_error", error=str(exc))
        envelope = ErrorEnvelope(
            error="database_error",
            detail="persistence error",
            status_code=500,
        )
        return JSONResponse(status_code=500, content=envelope.model_dump())

    if isinstance(exc, EvaluationError):
        logger.error("evaluation_error", error=str(exc))
        envelope = ErrorEnvelope(
            error="evaluation_error",
            detail="evaluation error",
            status_code=500,
        )
        return JSONResponse(status_code=500, content=envelope.model_dump())

    logger.error("unhandled_error", error=str(exc), error_type=type(exc).__name__)
    envelope = ErrorEnvelope(
        error="internal_error",
        detail="internal error",
        status_code=500,
    )
    return JSONResponse(status_code=500, content=envelope.model_dump())


async def access_logging_middleware(request: Request, call_next):
    """Structured access logging for every request."""
    start = time.perf_counter_ns()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter_ns() - start) / 1_000_000
    logger.info(
        "api_access",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        elapsed_ms=round(elapsed_ms, 1),
    )
    return response


def register_middleware(app: FastAPI) -> None:
    """Register all middleware on the FastAPI app."""
    app.add_exception_handler(RequestValidationError, global_error_handler)
    app.add_exception_handler(DatabaseError, global_error_handler)
    app.add_exception_handler(EvaluationError, global_error_handler)
    app.add_exception_handler(Exception, global_error_handler)
    app.middleware("http")(access_logging_middleware)
