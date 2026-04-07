"""Structured JSON logging with sensitive field redaction for MRAG.

Configures structlog with a processor pipeline that produces JSON lines output
with ISO 8601 timestamps, log levels, module names, and automatic redaction
of sensitive fields.
"""

from __future__ import annotations

import logging
from typing import Any

import structlog

SENSITIVE_KEY_PATTERNS = (
    "api_key",
    "secret",
    "password",
    "token",
    "credential",
    "database_url",
)


def redact_sensitive_keys(
    logger: Any, method_name: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    """Redact values matching sensitive key patterns."""
    for key in list(event_dict.keys()):
        key_lower = key.lower()
        if any(pattern in key_lower for pattern in SENSITIVE_KEY_PATTERNS):
            event_dict[key] = "***"
    return event_dict


def configure_logging(log_level: str = "INFO") -> None:
    """Configure the global structlog pipeline.

    Must be called once at application startup. Sets up the processor chain:
    add_log_level -> TimeStamper -> redact_sensitive_keys -> JSONRenderer.
    """
    level = getattr(logging, log_level.upper(), logging.INFO)
    logging.basicConfig(format="%(message)s", level=level, force=True)

    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            redact_sensitive_keys,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Return a structured logger bound to the given module name."""
    return structlog.get_logger(name, module=name)
