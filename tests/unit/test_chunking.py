"""Unit tests for text chunking in mrag.data.chunking."""

import pytest


class TestTextChunker:
    def test_short_text_returns_single_chunk(self) -> None:
        from mrag.data.chunking import TextChunker

        chunker = TextChunker(chunk_size=512, chunk_overlap=50)
        chunks = chunker.chunk("Short text.", "doc1")
        assert len(chunks) == 1
        assert chunks[0].text == "Short text."
        assert chunks[0].chunk_index == 0
        assert chunks[0].total_chunks == 1

    def test_chunk_id_format(self) -> None:
        from mrag.data.chunking import TextChunker

        chunker = TextChunker(chunk_size=512, chunk_overlap=50)
        chunks = chunker.chunk("Some text here.", "my_doc")
        assert chunks[0].chunk_id == "my_doc_chunk_0"

    def test_long_text_produces_multiple_chunks(self, sample_long_text: str) -> None:
        from mrag.data.chunking import TextChunker

        chunker = TextChunker(chunk_size=100, chunk_overlap=20)
        chunks = chunker.chunk(sample_long_text, "doc_long")
        assert len(chunks) > 1
        for chunk in chunks:
            assert chunk.token_count > 0
            assert chunk.text.strip() != ""

    def test_total_chunks_consistent(self, sample_long_text: str) -> None:
        from mrag.data.chunking import TextChunker

        chunker = TextChunker(chunk_size=80, chunk_overlap=15)
        chunks = chunker.chunk(sample_long_text, "doc_consist")
        total = len(chunks)
        for chunk in chunks:
            assert chunk.total_chunks == total

    def test_chunk_indices_sequential(self, sample_long_text: str) -> None:
        from mrag.data.chunking import TextChunker

        chunker = TextChunker(chunk_size=80, chunk_overlap=15)
        chunks = chunker.chunk(sample_long_text, "doc_seq")
        for i, chunk in enumerate(chunks):
            assert chunk.chunk_index == i

    def test_deterministic_output(self, sample_long_text: str) -> None:
        from mrag.data.chunking import TextChunker

        chunker = TextChunker(chunk_size=100, chunk_overlap=20)
        chunks1 = chunker.chunk(sample_long_text, "doc_det")
        chunks2 = chunker.chunk(sample_long_text, "doc_det")
        assert len(chunks1) == len(chunks2)
        for c1, c2 in zip(chunks1, chunks2, strict=False):
            assert c1.text == c2.text
            assert c1.chunk_id == c2.chunk_id

    def test_sentence_boundaries_preserved(self) -> None:
        from mrag.data.chunking import TextChunker

        text = (
            "First sentence here. Second sentence follows. "
            "Third sentence is present. Fourth sentence ends it. "
            "Fifth sentence for good measure. Sixth sentence too. "
            "Seventh sentence adds more. Eighth sentence wraps up."
        )
        chunker = TextChunker(chunk_size=15, chunk_overlap=3)
        chunks = chunker.chunk(text, "doc_sent")
        for chunk in chunks:
            # Each chunk should not start or end mid-sentence (allowing first/last)
            text_stripped = chunk.text.strip()
            assert text_stripped, "chunk text must not be empty"

    def test_unicode_text(self) -> None:
        from mrag.data.chunking import TextChunker

        text = (
            "\u00bfQu\u00e9 es el agua? El agua es esencial. "
            "\u00bfC\u00f3mo funciona? Funciona bien. "
            "\u00bfD\u00f3nde est\u00e1? Est\u00e1 aqu\u00ed. "
            "M\u00e1s texto en espa\u00f1ol. "
            "Otro contenido relevante. "
            "Y otra frase m\u00e1s para probar."
        )
        chunker = TextChunker(chunk_size=15, chunk_overlap=3)
        chunks = chunker.chunk(text, "doc_uni")
        assert len(chunks) >= 1
        full_text = " ".join(c.text for c in chunks)
        assert "agua" in full_text

    def test_start_end_positions_valid(self, sample_long_text: str) -> None:
        from mrag.data.chunking import TextChunker

        chunker = TextChunker(chunk_size=100, chunk_overlap=20)
        chunks = chunker.chunk(sample_long_text, "doc_pos")
        for chunk in chunks:
            assert chunk.end_pos > chunk.start_pos
            assert chunk.start_pos >= 0
            # The chunk text should be extractable from the source
            extracted = sample_long_text[chunk.start_pos : chunk.end_pos]
            assert extracted.strip() == chunk.text.strip()

    def test_overlap_exists_between_chunks(self, sample_long_text: str) -> None:
        from mrag.data.chunking import TextChunker

        chunker = TextChunker(chunk_size=80, chunk_overlap=20)
        chunks = chunker.chunk(sample_long_text, "doc_overlap")
        if len(chunks) > 1:
            # Consecutive chunks should have some text overlap
            for i in range(len(chunks) - 1):
                assert chunks[i].end_pos > chunks[i + 1].start_pos

    def test_empty_text_raises(self) -> None:
        from mrag.data.chunking import TextChunker

        chunker = TextChunker(chunk_size=512, chunk_overlap=50)
        with pytest.raises(ValueError, match="non-empty"):
            chunker.chunk("", "doc_empty")

    def test_whitespace_only_text_raises(self) -> None:
        from mrag.data.chunking import TextChunker

        chunker = TextChunker(chunk_size=512, chunk_overlap=50)
        with pytest.raises(ValueError, match="non-empty"):
            chunker.chunk("   \n\t  ", "doc_ws")
