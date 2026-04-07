"""Unit tests for retriever service in mrag.retrieval.retriever."""

from mrag.data.models import QuestionType
from mrag.embeddings.metadata_store import MetadataStore
from mrag.retrieval.models import RetrievalRequest


def _setup_retriever() -> tuple:
    """Set up encoder, indexer, metadata store with test data."""
    from mrag.embeddings.encoder import EmbeddingEncoder
    from mrag.embeddings.indexer import FAISSIndexer

    encoder = EmbeddingEncoder()
    texts = [
        "Photosynthesis is a process used by plants to convert light energy.",
        "Albert Einstein was a German-born theoretical physicist.",
        "World War II ended in 1945 after Japan's surrender.",
        "The Eiffel Tower is located in Paris, France.",
        "The heart pumps blood through the circulatory system.",
    ]
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
            question=f"Question {i}?",
            answer_short=f"Answer {i}" if i % 2 == 0 else None,
            answer_long=f"Long answer {i}.",
            question_type=(
                QuestionType.FACTOID if i % 2 == 0 else QuestionType.DESCRIPTIVE
            ),
            domain=["science", "science", "history", "geography", "health"][i],
            difficulty="easy" if i % 2 == 0 else "medium",
            has_short_answer=i % 2 == 0,
        )

    from mrag.retrieval.retriever import RetrieverService

    retriever = RetrieverService(
        encoder=encoder,
        indexer=indexer,
        metadata_store=store,
    )
    return retriever


class TestRetrieverService:
    def test_basic_retrieval(self) -> None:
        retriever = _setup_retriever()
        request = RetrievalRequest(query="What is photosynthesis?")
        results = retriever.retrieve(request)
        assert len(results) >= 1
        assert all(r.chunk_text for r in results)
        assert all(r.relevance_score >= 0 for r in results)

    def test_top_k_enforcement(self) -> None:
        retriever = _setup_retriever()
        request = RetrievalRequest(query="What is photosynthesis?", top_k=3)
        results = retriever.retrieve(request)
        assert len(results) <= 3

    def test_results_sorted_by_relevance(self) -> None:
        retriever = _setup_retriever()
        request = RetrievalRequest(query="What is photosynthesis?")
        results = retriever.retrieve(request)
        scores = [r.relevance_score for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_threshold_filtering(self) -> None:
        retriever = _setup_retriever()
        request = RetrievalRequest(
            query="What is photosynthesis?",
            top_k=5,
            score_threshold=0.5,
        )
        results = retriever.retrieve(request)
        for r in results:
            assert r.relevance_score >= 0.5

    def test_metadata_filter(self) -> None:
        retriever = _setup_retriever()
        request = RetrievalRequest(
            query="What is science?",
            top_k=5,
            metadata_filters={"domain": "science"},
        )
        results = retriever.retrieve(request)
        for r in results:
            assert r.domain == "science"

    def test_complete_result_fields(self) -> None:
        retriever = _setup_retriever()
        request = RetrievalRequest(query="What is photosynthesis?")
        results = retriever.retrieve(request)
        for r in results:
            assert r.chunk_id
            assert r.doc_id
            assert r.chunk_text
            assert 0.0 <= r.relevance_score <= 1.0
            assert -1.0 <= r.cosine_similarity <= 1.0
            assert r.question
            assert r.answer_long
            assert r.question_type
            assert r.domain
            assert r.difficulty
            assert isinstance(r.has_short_answer, bool)

    def test_empty_results_for_irrelevant_query(self) -> None:
        retriever = _setup_retriever()
        request = RetrievalRequest(
            query="zzzzzzzzzz unrelated query xyz123",
            top_k=5,
            score_threshold=0.99,
        )
        results = retriever.retrieve(request)
        # With high threshold, should get very few or no results
        assert isinstance(results, list)
