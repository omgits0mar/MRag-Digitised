"""Unit tests for metadata store in mrag.embeddings.metadata_store."""

from typing import Any

import pytest

from mrag.data.models import Difficulty, QuestionType


class TestMetadataStore:
    @pytest.fixture()
    def store_with_entries(self) -> None:
        from mrag.embeddings.metadata_store import MetadataStore

        store = MetadataStore()
        for i in range(5):
            store.add(
                faiss_id=i,
                chunk_id=f"doc1_chunk_{i}",
                doc_id="doc1",
                chunk_text=f"Chunk text {i}",
                question="What is X?",
                answer_short="Answer",
                answer_long="A long answer.",
                question_type=QuestionType.FACTOID,
                domain="science" if i < 3 else "history",
                difficulty=Difficulty.EASY,
                has_short_answer=True,
            )
        return store

    def test_add_and_get(self) -> None:
        from mrag.embeddings.metadata_store import MetadataStore

        store = MetadataStore()
        store.add(
            faiss_id=0,
            chunk_id="c0",
            doc_id="d0",
            chunk_text="text",
            question="Q?",
            answer_short="A",
            answer_long="Long A",
            question_type=QuestionType.FACTOID,
            domain="science",
            difficulty=Difficulty.EASY,
            has_short_answer=True,
        )
        entry = store.get(0)
        assert entry.chunk_id == "c0"
        assert entry.question == "Q?"
        assert entry.domain == "science"

    def test_get_nonexistent_raises(self) -> None:
        from mrag.embeddings.metadata_store import MetadataStore

        store = MetadataStore()
        with pytest.raises(KeyError):
            store.get(999)

    def test_filter_by_domain(self) -> None:
        from mrag.embeddings.metadata_store import MetadataStore

        store = MetadataStore()
        for i in range(5):
            store.add(
                faiss_id=i,
                chunk_id=f"c{i}",
                doc_id="d1",
                chunk_text=f"text {i}",
                question="Q?",
                answer_short="A",
                answer_long="Long",
                question_type=QuestionType.FACTOID,
                domain="science" if i < 3 else "history",
                difficulty=Difficulty.EASY,
                has_short_answer=True,
            )

        science_ids = store.filter("domain", "science")
        assert len(science_ids) == 3
        assert all(i in science_ids for i in [0, 1, 2])

    def test_filter_no_match(self) -> None:
        from mrag.embeddings.metadata_store import MetadataStore

        store = MetadataStore()
        store.add(
            faiss_id=0,
            chunk_id="c0",
            doc_id="d0",
            chunk_text="text",
            question="Q?",
            answer_short="A",
            answer_long="Long",
            question_type=QuestionType.FACTOID,
            domain="science",
            difficulty=Difficulty.EASY,
            has_short_answer=True,
        )

        result = store.filter("domain", "nonexistent")
        assert result == []

    def test_save_load_roundtrip(self, tmp_path: Any) -> None:
        from mrag.embeddings.metadata_store import MetadataStore

        store = MetadataStore()
        store.add(
            faiss_id=0,
            chunk_id="c0",
            doc_id="d0",
            chunk_text="text",
            question="Q?",
            answer_short="A",
            answer_long="Long A",
            question_type=QuestionType.FACTOID,
            domain="science",
            difficulty=Difficulty.EASY,
            has_short_answer=True,
        )

        path = str(tmp_path / "metadata.json")
        store.save(path)

        store2 = MetadataStore()
        store2.load(path)

        entry = store2.get(0)
        assert entry.chunk_id == "c0"
        assert entry.domain == "science"
        assert entry.question_type == QuestionType.FACTOID

    def test_load_nonexistent_raises(self) -> None:
        from mrag.embeddings.metadata_store import MetadataStore

        store = MetadataStore()
        with pytest.raises(FileNotFoundError):
            store.load("/nonexistent/path.json")
