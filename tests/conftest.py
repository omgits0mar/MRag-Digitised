"""Shared test fixtures for MRAG test suite."""

from typing import Any

import pytest


@pytest.fixture()
def temp_env(monkeypatch: pytest.MonkeyPatch) -> dict[str, str]:
    """Provide temporary environment variable overrides.

    Returns a dict that can be used to set env vars via monkeypatch.
    Automatically cleans up after the test.
    """
    overrides: dict[str, str] = {}
    for key, value in overrides.items():
        monkeypatch.setenv(key, value)
    return overrides


@pytest.fixture()
def temp_dir(tmp_path: Any) -> Any:
    """Provide a temporary directory that is cleaned up after the test."""
    return tmp_path


@pytest.fixture()
def sample_config_dict() -> dict[str, Any]:
    """Provide a sample configuration dictionary with all required fields."""
    return {
        "app_name": "mrag",
        "app_version": "0.1.0",
        "debug": False,
        "log_level": "INFO",
        "embedding_model_name": "paraphrase-multilingual-MiniLM-L12-v2",
        "embedding_dimension": 384,
        "chunk_size": 512,
        "chunk_overlap": 50,
        "top_k": 5,
        "faiss_index_type": "Flat",
        "llm_api_url": "https://api.groq.com/openai/v1",
        "llm_api_key": "test-key-for-unit-tests",
        "llm_model_name": "llama3-8b-8192",
        "llm_temperature": 0.1,
        "llm_max_tokens": 1024,
        "database_url": "sqlite:///test.db",
        "cache_ttl_seconds": 3600,
        "cache_max_size": 1000,
        "data_dir": "data",
        "prompts_dir": "prompts/templates",
    }
