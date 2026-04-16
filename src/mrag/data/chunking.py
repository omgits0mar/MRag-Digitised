"""Text chunking with sliding window and sentence-boundary alignment.

Splits long-form text into retrieval-optimized chunks with configurable
size and overlap. Sentence boundaries are preserved to maintain semantic
coherence within chunks.
"""

from __future__ import annotations

import re
import unicodedata

import structlog

from mrag.data.models import TextChunk

logger = structlog.get_logger(__name__)

# Sentence-ending punctuation with optional closing quotes/brackets
_SENTENCE_END_RE = re.compile(r"[.!?。！？][\"')\]」』]?")


class TextChunker:
    """Configurable text chunker with sentence-boundary alignment.

    Args:
        chunk_size: Maximum number of whitespace-separated tokens per chunk.
        chunk_overlap: Number of tokens to overlap between consecutive chunks.
    """

    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 50) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be > 0")
        if chunk_overlap < 0:
            raise ValueError("chunk_overlap must be >= 0")
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be < chunk_size")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk(self, text: str, doc_id: str) -> list[TextChunk]:
        """Split text into overlapping, sentence-boundary-aligned chunks.

        Args:
            text: Source text to chunk.
            doc_id: Parent document ID for chunk ID generation.

        Returns:
            List of TextChunk objects (minimum 1).

        Raises:
            ValueError: If text is empty or whitespace-only.
        """
        normalized = unicodedata.normalize("NFC", text)
        stripped = normalized.strip()
        if not stripped:
            raise ValueError("text must be non-empty after stripping whitespace")

        # If the entire text fits in one chunk, return it directly
        tokens = stripped.split()
        if len(tokens) <= self.chunk_size:
            return [
                TextChunk(
                    chunk_id=f"{doc_id}_chunk_0",
                    doc_id=doc_id,
                    text=stripped,
                    start_pos=0,
                    end_pos=len(text),
                    token_count=len(tokens),
                    chunk_index=0,
                    total_chunks=1,
                )
            ]

        # Split text into sentences for boundary alignment
        sentences = self._split_sentences(stripped)
        chunks = self._build_chunks(sentences, stripped, doc_id)

        logger.debug(
            "text_chunked",
            doc_id=doc_id,
            total_chunks=len(chunks),
            total_tokens=len(tokens),
        )
        return chunks

    def _split_sentences(self, text: str) -> list[str]:
        """Split text into sentences using punctuation boundaries.

        Uses a simple approach: split on sentence-ending punctuation
        followed by a space and an uppercase letter or end of text.
        """
        # Split on sentence-ending punctuation followed by whitespace
        parts = _SENTENCE_END_RE.split(text)

        # Re-attach the punctuation that was removed by the split
        sentences: list[str] = []
        pos = 0
        for part in parts:
            part = part.strip()
            if not part:
                continue
            # Find where this part starts in the original text
            idx = text.find(part, pos)
            if idx == -1:
                # Fallback: just use the part as-is
                sentences.append(part)
                continue

            end_idx = idx + len(part)
            # Look ahead for the sentence-ending punctuation
            remaining = text[end_idx:].lstrip()
            if remaining:
                # Check if next chars are sentence-ending punctuation
                for sep in (".", "!", "?", "\u3002", "\uff01", "\uff1f"):
                    if remaining.startswith(sep):
                        end_idx = text.find(sep, end_idx) + 1
                        # Also consume closing quotes/brackets
                        rest = text[end_idx:]
                        if rest and rest[0] in "\"')]\u300d\u3011":
                            end_idx += 1
                        break

            sentence = text[idx:end_idx].strip()
            if sentence:
                sentences.append(sentence)
            pos = end_idx

        if not sentences:
            sentences = [text]

        return sentences

    def _build_chunks(
        self, sentences: list[str], original_text: str, doc_id: str
    ) -> list[TextChunk]:
        """Build chunks from sentences using a sliding window approach."""
        chunks: list[TextChunk] = []
        # Track sentence positions in original text for start_pos/end_pos
        sentence_positions = self._get_sentence_positions(sentences, original_text)

        # Group sentences into chunks respecting chunk_size
        chunk_groups: list[list[int]] = []  # indices into sentences
        current_group: list[int] = []
        current_tokens = 0

        for i, sent in enumerate(sentences):
            sent_tokens = len(sent.split())
            if current_tokens + sent_tokens > self.chunk_size and current_group:
                chunk_groups.append(current_group)
                # Step back by overlap
                overlap_tokens = 0
                overlap_start = len(current_group)
                for j in range(len(current_group) - 1, -1, -1):
                    overlap_tokens += len(sentences[current_group[j]].split())
                    if overlap_tokens >= self.chunk_overlap:
                        overlap_start = j
                        break
                current_group = list(current_group[overlap_start:])
                current_tokens = sum(
                    len(sentences[idx].split()) for idx in current_group
                )
            current_group.append(i)
            current_tokens += sent_tokens

        if current_group:
            chunk_groups.append(current_group)

        total = len(chunk_groups)
        for chunk_idx, group in enumerate(chunk_groups):
            chunk_text = " ".join(sentences[i] for i in group)
            token_count = len(chunk_text.split())

            # Find positions in original text
            first_sent_idx = group[0]
            last_sent_idx = group[-1]
            start_pos = sentence_positions[first_sent_idx][0]
            end_pos = sentence_positions[last_sent_idx][1]

            chunks.append(
                TextChunk(
                    chunk_id=f"{doc_id}_chunk_{chunk_idx}",
                    doc_id=doc_id,
                    text=chunk_text,
                    start_pos=start_pos,
                    end_pos=end_pos,
                    token_count=token_count,
                    chunk_index=chunk_idx,
                    total_chunks=total,
                )
            )

        return chunks

    def _get_sentence_positions(
        self, sentences: list[str], original_text: str
    ) -> list[tuple[int, int]]:
        """Find (start, end) positions of each sentence in the original text."""
        positions: list[tuple[int, int]] = []
        search_start = 0
        for sent in sentences:
            # Find the sentence text in the original
            idx = original_text.find(sent, search_start)
            if idx == -1:
                # Approximate: use current search_start
                idx = search_start
            end = idx + len(sent)
            positions.append((idx, min(end, len(original_text))))
            search_start = end
        return positions
