"""Unit tests for mrag.exceptions — Hierarchy, inheritance, detail field."""

import pytest

from mrag.exceptions import (
    APIError,
    CacheError,
    DatabaseError,
    DataProcessingError,
    EmbeddingError,
    EvaluationError,
    MRAGError,
    QueryProcessingError,
    ResponseGenerationError,
    RetrievalError,
)


class TestMRAGError:
    """Test the base MRAGError class."""

    def test_inherits_from_exception(self) -> None:
        assert issubclass(MRAGError, Exception)

    def test_str_returns_message(self) -> None:
        e = MRAGError("something went wrong")
        assert str(e) == "something went wrong"

    def test_message_attribute(self) -> None:
        e = MRAGError("test message")
        assert e.message == "test message"

    def test_detail_defaults_to_none(self) -> None:
        e = MRAGError("msg")
        assert e.detail is None

    def test_detail_stores_dict(self) -> None:
        e = MRAGError("msg", {"key": "value"})
        assert e.detail == {"key": "value"}


class TestSubclasses:
    """Test all 9 module-specific exception subclasses."""

    subclasses = [
        DataProcessingError,
        EmbeddingError,
        RetrievalError,
        QueryProcessingError,
        ResponseGenerationError,
        CacheError,
        APIError,
        DatabaseError,
        EvaluationError,
    ]

    @pytest.mark.parametrize("cls", subclasses)
    def test_inherits_from_mrag_error(self, cls: type) -> None:
        assert issubclass(cls, MRAGError)

    @pytest.mark.parametrize("cls", subclasses)
    def test_inherits_from_exception(self, cls: type) -> None:
        assert issubclass(cls, Exception)

    @pytest.mark.parametrize("cls", subclasses)
    def test_str_returns_message(self, cls: type) -> None:
        e = cls("module error")
        assert str(e) == "module error"

    @pytest.mark.parametrize("cls", subclasses)
    def test_detail_stores_dict(self, cls: type) -> None:
        e = cls("msg", {"index": "missing"})
        assert e.detail == {"index": "missing"}

    def test_all_nine_subclasses_present(self) -> None:
        assert len(self.subclasses) == 9


class TestCatching:
    """Test catching via base class."""

    def test_catching_subclass_via_base(self) -> None:
        with pytest.raises(MRAGError):
            raise RetrievalError("not found", {"index": "missing"})

    def test_catching_specific_subclass(self) -> None:
        with pytest.raises(RetrievalError):
            raise RetrievalError("vector search failed")

    def test_exception_details_preserved(self) -> None:
        try:
            raise RetrievalError("not found", {"index": "missing"})
        except MRAGError as e:
            assert str(e) == "not found"
            assert e.detail == {"index": "missing"}


class TestImportability:
    """Test all exceptions are importable from mrag.exceptions."""

    def test_all_importable(self) -> None:
        from mrag.exceptions import (
            APIError,
            CacheError,
            DatabaseError,
            DataProcessingError,
            EmbeddingError,
            EvaluationError,
            MRAGError,
            QueryProcessingError,
            ResponseGenerationError,
            RetrievalError,
        )

        assert all(
            cls is not None
            for cls in [
                MRAGError,
                DataProcessingError,
                EmbeddingError,
                RetrievalError,
                QueryProcessingError,
                ResponseGenerationError,
                CacheError,
                APIError,
                DatabaseError,
                EvaluationError,
            ]
        )
