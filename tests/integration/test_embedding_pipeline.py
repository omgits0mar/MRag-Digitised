"""Integration test for the embedding pipeline: embed -> index -> search."""

from typing import Any

import pytest

from mrag.data.models import (
    AnswerType,
    Difficulty,
    DocumentMetadata,
    ProcessedDocument,
    QuestionType,
    TextChunk,
)


def _make_test_documents(count: int = 10) -> list[ProcessedDocument]:
    """Create test documents for embedding pipeline."""
    docs = []
    for i in range(count):
        chunk = TextChunk(
            chunk_id=f"doc{i}_chunk_0",
            doc_id=f"doc{i}",
            text=f"This is test document number {i} about science and history.",
            start_pos=0,
            end_pos=60,
            token_count=10,
            chunk_index=0,
            total_chunks=1,
        )
        meta = DocumentMetadata(
            question_type=(
                QuestionType.FACTOID if i % 2 == 0 else QuestionType.DESCRIPTIVE
            ),
            domain="science" if i % 3 == 0 else "history",
            difficulty=Difficulty.EASY if i % 2 == 0 else Difficulty.MEDIUM,
            has_short_answer=i % 2 == 0,
            source_id=f"src_{i}",
        )
        doc = ProcessedDocument(
            doc_id=f"doc{i}",
            question=f"What is test {i}?",
            answer_short=f"Test answer {i}" if i % 2 == 0 else None,
            answer_long=f"This is the long answer for test document {i}.",
            answer_type=AnswerType.BOTH if i % 2 == 0 else AnswerType.LONG,
            chunks=[chunk],
            metadata=meta,
        )
        docs.append(doc)
    return docs


class TestEmbeddingPipelineIntegration:
    def test_embed_index_search_roundtrip(
        self, sample_csv_file: str, tmp_path: Any, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test: create docs -> embed -> build index -> search -> verify results."""
        from mrag.embeddings.encoder import EmbeddingEncoder
        from mrag.embeddings.indexer import FAISSIndexer
        from mrag.embeddings.metadata_store import MetadataStore

        docs = _make_test_documents(10)

        # Extract chunks and metadata
        chunk_texts = []
        for doc in docs:
            for chunk in doc.chunks:
                chunk_texts.append(chunk.text)

        # Embed
        encoder = EmbeddingEncoder()
        embeddings = encoder.encode(chunk_texts)
        assert embeddings.shape[0] == 10
        assert embeddings.shape[1] == 384

        # Build index
        indexer = FAISSIndexer(dimension=384)
        indexer.build_index(embeddings)
        assert indexer.ntotal == 10

        # Search
        query_embedding = encoder.encode_single(chunk_texts[0])
        scores, indices = indexer.search(query_embedding, top_k=5)
        assert len(scores) == 5
        assert indices[0] == 0  # First result should be the query itself
        assert scores[0] > 0.99

        # Metadata store roundtrip
        store = MetadataStore()
        for i, doc in enumerate(docs):
            for chunk in doc.chunks:
                store.add(
                    faiss_id=i,
                    chunk_id=chunk.chunk_id,
                    doc_id=doc.doc_id,
                    chunk_text=chunk.text,
                    question=doc.question,
                    answer_short=doc.answer_short,
                    answer_long=doc.answer_long,
                    question_type=doc.metadata.question_type,
                    domain=doc.metadata.domain,
                    difficulty=doc.metadata.difficulty,
                    has_short_answer=doc.metadata.has_short_answer,
                )

        # Verify metadata retrieval for search results
        for idx in indices:
            entry = store.get(int(idx))
            assert entry.chunk_text != ""

        # Save/load persistence
        meta_path = str(tmp_path / "metadata.json")
        index_path = str(tmp_path / "index.faiss")

        store.save(meta_path)
        indexer.save(index_path)

        # Reload and verify
        store2 = MetadataStore()
        store2.load(meta_path)
        assert store2.get(0).chunk_id == "doc0_chunk_0"

        indexer2 = FAISSIndexer(dimension=384)
        indexer2.load(index_path)
        scores2, indices2 = indexer2.search(query_embedding, top_k=3)
        assert indices2[0] == 0
