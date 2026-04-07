"""Integration test for the full data processing pipeline."""

import json
from pathlib import Path
from typing import Any

import pytest

from mrag.config import Settings


def _make_config(tmp_path: Any, monkeypatch: pytest.MonkeyPatch) -> Settings:
    """Create a Settings instance for testing with tmp_path as data_dir."""
    monkeypatch.setenv("LLM_API_KEY", "test-key-for-integration-tests")
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    # Reset singleton so new Settings is created
    import mrag.config as config_mod

    config_mod._settings_instance = None
    return Settings(data_dir=str(tmp_path / "data"))


class TestDataPipelineIntegration:
    def test_full_pipeline_end_to_end(
        self, sample_csv_file: str, tmp_path: Any, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test ingest -> chunk -> enrich -> export on 10-row sample."""
        from mrag.data.pipeline import run_pipeline

        raw_dir = tmp_path / "data" / "raw"
        raw_dir.mkdir(parents=True)
        (tmp_path / "data" / "processed").mkdir(parents=True)

        import shutil

        shutil.copy(sample_csv_file, str(raw_dir / "sample.csv"))

        config = _make_config(tmp_path, monkeypatch)
        result = run_pipeline(config)

        assert result.valid_records == 10
        assert result.total_chunks >= 10
        assert result.train_file is not None
        assert result.eval_file is not None
        assert Path(result.train_file).exists()
        assert Path(result.eval_file).exists()
        assert result.elapsed_seconds >= 0

    def test_output_jsonl_structure(
        self, sample_csv_file: str, tmp_path: Any, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Verify JSONL output has correct structure."""
        from mrag.data.pipeline import run_pipeline

        raw_dir = tmp_path / "data" / "raw"
        raw_dir.mkdir(parents=True)
        (tmp_path / "data" / "processed").mkdir(parents=True)

        import shutil

        shutil.copy(sample_csv_file, str(raw_dir / "sample.csv"))

        config = _make_config(tmp_path, monkeypatch)
        result = run_pipeline(config)

        train_path = result.train_file
        assert train_path is not None
        with open(train_path, encoding="utf-8") as f:
            for line in f:
                doc = json.loads(line)
                assert "doc_id" in doc
                assert "question" in doc
                assert "answer_long" in doc
                assert "answer_type" in doc
                assert "chunks" in doc
                assert len(doc["chunks"]) >= 1
                assert "metadata" in doc
                assert "question_type" in doc["metadata"]
                assert "domain" in doc["metadata"]
                assert "difficulty" in doc["metadata"]

    def test_pipeline_preserves_all_records(
        self, sample_csv_file: str, tmp_path: Any, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Verify no data loss through the pipeline."""
        from mrag.data.pipeline import run_pipeline

        raw_dir = tmp_path / "data" / "raw"
        raw_dir.mkdir(parents=True)
        (tmp_path / "data" / "processed").mkdir(parents=True)

        import shutil

        shutil.copy(sample_csv_file, str(raw_dir / "sample.csv"))

        config = _make_config(tmp_path, monkeypatch)
        result = run_pipeline(config)

        total_in_output = result.train_count + result.eval_count
        assert total_in_output == result.valid_records
