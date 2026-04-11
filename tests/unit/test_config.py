"""Unit tests for mrag.config — Settings loading, validation, immutability."""

from typing import Any

import pytest
from pydantic import ValidationError

from mrag.config import Settings, get_settings


# Reset singleton between tests
@pytest.fixture(autouse=True)
def _reset_settings() -> None:
    import mrag.config as cfg

    cfg._settings_instance = None


class TestSettingsDefaults:
    """Test that Settings loads with defaults when env vars are set."""

    def test_loads_with_defaults(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("LLM_API_KEY", "test-key")
        s = Settings()
        assert s.app_name == "mrag"
        assert s.app_version == "0.1.0"
        assert s.debug is False
        assert s.log_level == "INFO"
        assert s.embedding_dimension == 384
        assert s.chunk_size == 512
        assert s.chunk_overlap == 50
        assert s.top_k == 5
        assert s.faiss_index_type == "Flat"
        assert s.llm_temperature == 0.1
        assert s.llm_max_tokens == 1024
        assert s.database_url.get_secret_value() == "sqlite+aiosqlite:///mrag.db"
        assert s.cache_ttl_seconds == 3600
        assert s.cache_max_size == 1000
        assert s.data_dir == "data"
        assert s.prompts_dir == "prompts/templates"

    def test_api_key_required(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            Settings()
        errors = exc_info.value.errors()
        field_names = [e["loc"][-1] for e in errors]
        assert "LLM_API_KEY" in field_names or "llm_api_key" in field_names


class TestEnvVarOverride:
    """Test environment variable precedence over defaults."""

    def test_env_var_overrides_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("LLM_API_KEY", "my-key")
        monkeypatch.setenv("TOP_K", "10")
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")
        s = Settings()
        assert s.llm_api_key.get_secret_value() == "my-key"
        assert s.top_k == 10
        assert s.log_level == "DEBUG"


class TestDotEnvFile:
    """Test .env file loading."""

    def test_loads_from_dotenv_file(
        self, tmp_path: Any, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        env_file = tmp_path / ".env"
        env_file.write_text("LLM_API_KEY=from-dotenv\nLOG_LEVEL=WARNING\n")
        monkeypatch.chdir(tmp_path)
        s = Settings()
        assert s.llm_api_key.get_secret_value() == "from-dotenv"
        assert s.log_level == "WARNING"

    def test_missing_dotenv_still_works(
        self, tmp_path: Any, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("LLM_API_KEY", "env-key")
        monkeypatch.chdir(tmp_path)
        s = Settings()
        assert s.llm_api_key.get_secret_value() == "env-key"


class TestTypeValidation:
    """Test type coercion and validation errors."""

    def test_string_where_int_expected(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("LLM_API_KEY", "key")
        monkeypatch.setenv("TOP_K", "not_a_number")
        with pytest.raises(ValidationError):
            Settings()


class TestAggregateErrors:
    """Test that multiple invalid fields produce aggregate ValidationError."""

    def test_multiple_errors_reported(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("LOG_LEVEL", "INVALID")
        monkeypatch.setenv("TOP_K", "0")
        monkeypatch.setenv("CHUNK_SIZE", "-1")
        with pytest.raises(ValidationError) as exc_info:
            Settings()
        errors = exc_info.value.errors()
        assert len(errors) >= 3


class TestImmutability:
    """Test that Settings is frozen after creation."""

    def test_frozen_raises_on_assignment(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("LLM_API_KEY", "key")
        s = Settings()
        with pytest.raises(ValidationError):
            s.top_k = 99  # type: ignore[misc]


class TestFieldValidators:
    """Test individual field validator constraints."""

    def test_invalid_log_level(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("LLM_API_KEY", "key")
        monkeypatch.setenv("LOG_LEVEL", "TRACE")
        with pytest.raises(ValidationError):
            Settings()

    def test_chunk_overlap_greater_than_size(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("LLM_API_KEY", "key")
        monkeypatch.setenv("CHUNK_SIZE", "10")
        monkeypatch.setenv("CHUNK_OVERLAP", "20")
        with pytest.raises(ValidationError):
            Settings()

    def test_chunk_overlap_equal_to_size(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("LLM_API_KEY", "key")
        monkeypatch.setenv("CHUNK_SIZE", "100")
        monkeypatch.setenv("CHUNK_OVERLAP", "100")
        with pytest.raises(ValidationError):
            Settings()

    def test_negative_chunk_overlap(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("LLM_API_KEY", "key")
        monkeypatch.setenv("CHUNK_OVERLAP", "-1")
        with pytest.raises(ValidationError):
            Settings()

    def test_zero_top_k(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("LLM_API_KEY", "key")
        monkeypatch.setenv("TOP_K", "0")
        with pytest.raises(ValidationError):
            Settings()

    def test_temperature_out_of_range(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("LLM_API_KEY", "key")
        monkeypatch.setenv("LLM_TEMPERATURE", "3.0")
        with pytest.raises(ValidationError):
            Settings()

    def test_invalid_faiss_index_type(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("LLM_API_KEY", "key")
        monkeypatch.setenv("FAISS_INDEX_TYPE", "INVALID")
        with pytest.raises(ValidationError):
            Settings()


class TestGetSettingsSingleton:
    """Test get_settings() singleton behavior."""

    def test_returns_same_instance(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("LLM_API_KEY", "key")
        s1 = get_settings()
        s2 = get_settings()
        assert s1 is s2

    def test_first_call_loads_second_returns_cached(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("LLM_API_KEY", "key")
        s1 = get_settings()
        monkeypatch.setenv("TOP_K", "20")
        s2 = get_settings()
        # Second call returns cached instance, env change ignored
        assert s2.top_k == s1.top_k


class TestSecretStrMasking:
    """Test that sensitive fields are not exposed in repr/str."""

    def test_api_key_not_in_repr(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("LLM_API_KEY", "super-secret-key")
        s = Settings()
        r = repr(s)
        assert "super-secret-key" not in r

    def test_api_key_not_in_str(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("LLM_API_KEY", "super-secret-key")
        s = Settings()
        assert "super-secret-key" not in str(s)
