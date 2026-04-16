"""SQLAlchemy declarative base for all ORM models."""

from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models.

    All persistence models in ``src/mrag/db/models.py`` inherit from this
    class so they share a single ``metadata`` object for schema creation.
    """
