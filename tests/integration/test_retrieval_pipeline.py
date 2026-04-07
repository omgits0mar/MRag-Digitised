"""Integration test for the full retrieval pipeline: query -> ranked results."""

import pytest

from mrag.embeddings.encoder import EmbeddingEncoder
from mrag.embeddings.indexer import FAISSIndexer
from mrag.embeddings.metadata_store import MetadataStore
from mrag.retrieval.models import RetrievalRequest
from mrag.retrieval.retriever import RetrieverService


def _build_test_index() -> RetrieverService:
    """Build a small test index with known content for retrieval testing."""
    texts = [
        "Photosynthesis is a process used by plants to "
        "convert light energy into chemical energy.",
        "Albert Einstein was a German-born theoretical "
        "physicist who developed relativity.",
        "World War II ended on September 2, 1945 when " "Japan formally surrendered.",
        "The Eiffel Tower is a wrought-iron lattice tower " "located in Paris, France.",
        "The human heart is a muscular organ that pumps "
        "blood through the circulatory system.",
        "DNA stands for deoxyribonucleic acid and carries " "genetic instructions.",
        "The Great Wall of China is a series of " "fortifications in northern China.",
        "Gravity is a fundamental force of nature that " "attracts objects with mass.",
    ]

    domains = [
        "science",
        "science",
        "history",
        "geography",
        "health",
        "science",
        "history",
        "science",
    ]
    q_types = [
        "factoid",
        "factoid",
        "factoid",
        "factoid",
        "descriptive",
        "factoid",
        "factoid",
        "descriptive",
    ]

    encoder = EmbeddingEncoder()
    embeddings = encoder.encode(texts)

    indexer = FAISSIndexer(dimension=384)
    indexer.build_index(embeddings)

    store = MetadataStore()
    for i, text in enumerate(texts):
        store.add(
            faiss_id=i,
            chunk_id=f"chunk_{i}",
            doc_id=f"doc_{i}",
            chunk_text=text,
            question=f"Question about {domains[i]} {i}?",
            answer_short=f"Short answer {i}" if i % 2 == 0 else None,
            answer_long=text,
            question_type=q_types[i],
            domain=domains[i],
            difficulty="easy" if i % 2 == 0 else "medium",
            has_short_answer=i % 2 == 0,
        )

    return RetrieverService(
        encoder=encoder,
        indexer=indexer,
        metadata_store=store,
    )


class TestRetrievalPipelineIntegration:
    @pytest.fixture()
    def retriever(self) -> RetrieverService:
        return _build_test_index()

    def test_biology_query_returns_science(self, retriever: RetrieverService) -> None:
        request = RetrievalRequest(query="What is photosynthesis?")
        results = retriever.retrieve(request)
        assert len(results) >= 1
        # First result should be about photosynthesis
        assert (
            "photosynthesis" in results[0].chunk_text.lower()
            or results[0].domain == "science"
        )

    def test_history_query(self, retriever: RetrieverService) -> None:
        request = RetrievalRequest(query="When did World War II end?")
        results = retriever.retrieve(request)
        assert len(results) >= 1
        # Should find WWII content in top results
        wwii_found = any(
            "war" in r.chunk_text.lower() or "1945" in r.chunk_text for r in results[:3]
        )
        assert wwii_found, (
            "Expected WWII content in top 3 results. "
            f"Got: {[r.chunk_text[:50] for r in results[:3]]}"
        )

    def test_metadata_filtering(self, retriever: RetrieverService) -> None:
        request = RetrievalRequest(
            query="What is science?",
            top_k=5,
            metadata_filters={"domain": "history"},
        )
        results = retriever.retrieve(request)
        for r in results:
            assert r.domain == "history"

    def test_complete_result_metadata(self, retriever: RetrieverService) -> None:
        request = RetrievalRequest(query="How does the heart work?")
        results = retriever.retrieve(request)
        assert len(results) >= 1
        r = results[0]
        assert r.chunk_id
        assert r.doc_id
        assert r.chunk_text
        assert 0.0 <= r.relevance_score <= 1.0
        assert -1.0 <= r.cosine_similarity <= 1.0
        assert r.question
        assert r.answer_long
        assert r.question_type in (
            "factoid",
            "descriptive",
            "list",
            "yes_no",
            "unknown",
        )
        assert r.domain
        assert r.difficulty in ("easy", "medium", "hard")
        assert isinstance(r.has_short_answer, bool)

    def test_results_ordered_by_relevance(self, retriever: RetrieverService) -> None:
        request = RetrievalRequest(query="What is photosynthesis?", top_k=5)
        results = retriever.retrieve(request)
        scores = [r.relevance_score for r in results]
        assert scores == sorted(scores, reverse=True), f"Scores not sorted: {scores}"
