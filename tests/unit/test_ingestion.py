"""Unit tests for dataset ingestion in mrag.data.ingestion."""

from typing import Any

import pytest

from mrag.data.models import RawRecord
from mrag.exceptions import DataProcessingError


class TestLoadDatasetCSV:
    def test_load_valid_csv(self, sample_csv_file: str) -> None:
        from mrag.data.ingestion import load_dataset

        records = load_dataset(sample_csv_file, file_format="csv")
        assert len(records) == 10
        assert all(isinstance(r, RawRecord) for r in records)

    def test_first_record_fields(self, sample_csv_file: str) -> None:
        from mrag.data.ingestion import load_dataset

        records = load_dataset(sample_csv_file, file_format="csv")
        first = records[0]
        assert "Einstein" in first.question_text
        assert first.short_answer is not None
        assert "physicist" in first.long_answer.lower()

    def test_whitespace_stripped_on_load(self, sample_csv_file: str) -> None:
        from mrag.data.ingestion import load_dataset

        records = load_dataset(sample_csv_file, file_format="csv")
        for r in records:
            assert r.question_text == r.question_text.strip()
            assert r.long_answer == r.long_answer.strip()


class TestLoadDatasetJSON:
    def test_load_valid_json(self, sample_json_file: str) -> None:
        from mrag.data.ingestion import load_dataset

        records = load_dataset(sample_json_file, file_format="json")
        assert len(records) == 10
        assert all(isinstance(r, RawRecord) for r in records)


class TestMalformedRecords:
    def test_malformed_records_skipped(
        self,
        sample_csv_with_malformed: str,
        tmp_path: Any,
    ) -> None:
        from mrag.data.ingestion import load_dataset

        path = tmp_path / "mixed.csv"
        path.write_text(sample_csv_with_malformed, encoding="utf-8")
        records = load_dataset(str(path), file_format="csv")
        assert len(records) == 10  # only the valid ones

    def test_missing_columns_csv(self, tmp_path: Any) -> None:
        from mrag.data.ingestion import load_dataset

        csv_content = "col_a,col_b\n1,2\n3,4\n"
        path = tmp_path / "bad_columns.csv"
        path.write_text(csv_content, encoding="utf-8")
        with pytest.raises(DataProcessingError):
            load_dataset(str(path), file_format="csv")

    def test_file_not_found(self) -> None:
        from mrag.data.ingestion import load_dataset

        with pytest.raises(DataProcessingError):
            load_dataset("/nonexistent/path.csv", file_format="csv")

    def test_all_records_malformed_raises(self, tmp_path: Any) -> None:
        from mrag.data.ingestion import load_dataset
        from mrag.exceptions import DataProcessingError

        csv_content = "question_text,short_answer,long_answer\ndata,,\n,more,\n"
        path = tmp_path / "all_bad.csv"
        path.write_text(csv_content, encoding="utf-8")
        with pytest.raises(DataProcessingError):
            load_dataset(str(path), file_format="csv")

    def test_empty_file_raises(self, tmp_path: Any) -> None:
        from mrag.data.ingestion import load_dataset
        from mrag.exceptions import DataProcessingError

        path = tmp_path / "empty.csv"
        path.write_text("", encoding="utf-8")
        with pytest.raises(DataProcessingError):
            load_dataset(str(path), file_format="csv")


class TestEncodingHandling:
    def test_utf8_content(self, tmp_path: Any) -> None:
        from mrag.data.ingestion import load_dataset

        csv_content = (
            "question_text,short_answer,long_answer\n"
            "\u00bfQu\u00e9 es el agua?,water,"
            "El agua es una sustancia esencial.\n"
        )
        path = tmp_path / "unicode.csv"
        path.write_text(csv_content, encoding="utf-8")
        records = load_dataset(str(path), file_format="csv")
        assert len(records) == 1
        assert "agua" in records[0].question_text
