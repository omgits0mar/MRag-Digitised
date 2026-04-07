"""Centralized configuration management for MRAG.

Provides typed, immutable settings loaded from environment variables and .env files
with aggregate validation via Pydantic BaseSettings.
"""

from __future__ import annotations

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Immutable application settings loaded from env vars / .env file.

    All fields have type annotations and defaults. Sensitive fields use SecretStr.
    Instance is frozen — attribute assignment raises ValidationError.
    """

    model_config = SettingsConfigDict(
        frozen=True,
        env_file=".env",
        env_file_encoding="utf-8",
    )

    # App
    app_name: str = "mrag"
    app_version: str = "0.1.0"
    debug: bool = False
    log_level: str = "INFO"

    # Embedding
    embedding_model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"
    embedding_dimension: int = 384

    # Chunking
    chunk_size: int = 512
    chunk_overlap: int = 50

    # Retrieval
    top_k: int = 5
    faiss_index_type: str = "Flat"

    # LLM
    llm_api_url: str = "https://api.groq.com/openai/v1"
    llm_api_key: SecretStr = Field(..., alias="LLM_API_KEY")
    llm_model_name: str = "llama3-8b-8192"
    llm_temperature: float = 0.1
    llm_max_tokens: int = 1024

    # Database
    database_url: SecretStr = SecretStr("sqlite:///mrag.db")

    # Cache
    cache_ttl_seconds: int = 3600
    cache_max_size: int = 1000

    # Paths
    data_dir: str = "data"
    prompts_dir: str = "prompts/templates"

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = v.upper()
        if upper not in allowed:
            raise ValueError(f"log_level must be one of {allowed}, got '{v}'")
        return upper

    @field_validator(
        "chunk_size",
        "embedding_dimension",
        "llm_max_tokens",
        "cache_ttl_seconds",
        "cache_max_size",
    )
    @classmethod
    def validate_positive_int(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("must be > 0")
        return v

    @field_validator("top_k")
    @classmethod
    def validate_top_k(cls, v: int) -> int:
        if v < 1:
            raise ValueError("must be >= 1")
        return v

    @field_validator("chunk_overlap")
    @classmethod
    def validate_chunk_overlap(cls, v: int) -> int:
        if v < 0:
            raise ValueError("must be >= 0")
        return v

    @field_validator("llm_temperature")
    @classmethod
    def validate_temperature(cls, v: float) -> float:
        if not (0.0 <= v <= 2.0):
            raise ValueError("must be >= 0.0 and <= 2.0")
        return v

    @field_validator("faiss_index_type")
    @classmethod
    def validate_faiss_index_type(cls, v: str) -> str:
        allowed = {"Flat", "IVF", "HNSW"}
        if v not in allowed:
            raise ValueError(f"must be one of {allowed}, got '{v}'")
        return v

    @model_validator(mode="after")
    def validate_chunk_overlap_lt_size(self) -> Settings:
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError(
                f"chunk_overlap ({self.chunk_overlap}) "
                f"must be < chunk_size ({self.chunk_size})"
            )
        return self


_settings_instance: Settings | None = None


def get_settings() -> Settings:
    """Return the singleton Settings instance.

    First call loads and validates configuration from env vars / .env.
    Subsequent calls return the cached instance.
    """
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()
    return _settings_instance
