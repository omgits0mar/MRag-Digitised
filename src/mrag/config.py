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
    llm_timeout_seconds: int = 30
    llm_max_retries: int = 3

    # Query Processing
    query_expansion_enabled: bool = True
    query_expansion_top_n: int = 3
    conversation_history_max_turns: int = 5

    # Generation
    confidence_threshold: float = 0.3

    # Database
    database_url: SecretStr = SecretStr("sqlite+aiosqlite:///mrag.db")
    db_pool_size: int = 5
    db_pool_max_overflow: int = 10
    db_echo: bool = False

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000"]
    )
    api_request_timeout_seconds: int = 30

    # Evaluation
    eval_heldout_path: str = "data/processed/eval.jsonl"
    eval_baseline_path: str = "data/evaluation/baseline_metrics.json"
    eval_report_dir: str = "data/reports"
    eval_k_values: list[int] = Field(default_factory=lambda: [1, 3, 5, 10])
    eval_benchmark_workload_size: int = 100
    eval_regression_threshold: float = 0.05

    # Cache
    cache_ttl_seconds: int = 3600
    cache_max_size: int = 1000

    # Paths
    data_dir: str = "data"
    prompts_dir: str = "prompts/templates"

    # File upload ingestion
    upload_dir: str = "data/uploads"
    upload_max_bytes: int = 100 * 1024 * 1024
    upload_allowed_extensions: list[str] = Field(
        default_factory=lambda: ["csv", "txt", "pdf", "md", "docx"]
    )

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
        "llm_timeout_seconds",
        "llm_max_retries",
        "query_expansion_top_n",
        "conversation_history_max_turns",
        "cache_ttl_seconds",
        "cache_max_size",
        "db_pool_size",
        "db_pool_max_overflow",
        "api_port",
        "api_request_timeout_seconds",
        "eval_benchmark_workload_size",
        "upload_max_bytes",
    )
    @classmethod
    def validate_positive_int(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("must be > 0")
        return v

    @field_validator("upload_allowed_extensions")
    @classmethod
    def normalize_upload_extensions(cls, v: list[str]) -> list[str]:
        normalized = [ext.strip().lstrip(".").lower() for ext in v]
        if not all(normalized):
            raise ValueError("upload_allowed_extensions entries must be non-empty")
        return normalized

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

    @field_validator("confidence_threshold")
    @classmethod
    def validate_confidence_threshold(cls, v: float) -> float:
        if not (0.0 <= v <= 1.0):
            raise ValueError("must be >= 0.0 and <= 1.0")
        return v

    @field_validator("eval_regression_threshold")
    @classmethod
    def validate_eval_regression_threshold(cls, v: float) -> float:
        if not (0.0 < v <= 1.0):
            raise ValueError("must be > 0.0 and <= 1.0")
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
