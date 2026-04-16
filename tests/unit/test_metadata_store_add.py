"""Tests for MetadataStore.add_entries and atomic save."""

from __future__ import annotations

from pathlib import Path

from mrag.embeddings.metadata_store import MetadataEntry, MetadataStore


def _make_entry(i: int) -> MetadataEntry:
    return MetadataEntry(
        faiss_index_id=i,
        chunk_id=f"chunk_{i}",
        doc_id=f"doc_{i}",
        chunk_text=f"text {i}",
        question="q",
        answer_short=None,
        answer_long=f"text {i}",
        question_type="unknown",
        domain="upload:txt",
        difficulty="medium",
        has_short_answer=False,
    )


def test_add_entries_appends_and_is_retrievable() -> None:
    store = MetadataStore()
    store.add_entries([_make_entry(0), _make_entry(1)])
    assert store.size == 2
    assert store.get(0).chunk_id == "chunk_0"
    assert store.get(1).chunk_id == "chunk_1"


def test_add_entries_overwrites_on_id_collision() -> None:
    store = MetadataStore()
    store.add_entries([_make_entry(0)])
    overwrite = _make_entry(0)
    overwrite.chunk_text = "updated"
    store.add_entries([overwrite])
    assert store.size == 1
    assert store.get(0).chunk_text == "updated"


def test_atomic_save_then_load_roundtrip(tmp_path: Path) -> None:
    store = MetadataStore()
    store.add_entries([_make_entry(0), _make_entry(1), _make_entry(2)])

    target = tmp_path / "metadata.json"
    store.save(str(target))
    assert target.exists()
    # Temp files from atomic save should be cleaned up
    leftovers = list(tmp_path.glob(".metadata_*.json.tmp"))
    assert leftovers == []

    reloaded = MetadataStore()
    reloaded.load(str(target))
    assert reloaded.size == 3
    assert reloaded.get(2).chunk_text == "text 2"
