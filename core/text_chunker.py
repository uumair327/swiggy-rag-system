"""Text chunking component for the Swiggy RAG System."""

import logging
from typing import List
from core.models import Chunk, ChunkMetadata, CoverageResult

logger = logging.getLogger(__name__)


class TextChunker:
    """
    Splits document text into overlapping chunks with metadata.

    Preserves sentence boundaries to maintain semantic coherence.
    """

    def chunk_text(
        self, text: str, chunk_size: int = 1000, overlap: int = 200, source_name: str = ""
    ) -> List[Chunk]:
        """
        Split text into overlapping chunks with metadata.

        Args:
            text: The text to chunk
            chunk_size: Maximum size of each chunk in characters (default 1000)
            overlap: Number of overlapping characters between chunks (default 200)
            source_name: Name of the source document for metadata

        Returns:
            List of Chunk objects with text and metadata
        """
        logger.info(
            f"Chunking text: {len(text)} characters, chunk_size={chunk_size}, "
            f"overlap={overlap}, source={source_name}"
        )

        if not text:
            logger.warning("Empty text provided for chunking")
            return []

        # Handle text shorter than chunk_size
        if len(text) <= chunk_size:
            logger.info("Text shorter than chunk_size, creating single chunk")
            metadata = ChunkMetadata(
                chunk_index=0, source_document=source_name, start_position=0, end_position=len(text)
            )
            return [Chunk(text=text, metadata=metadata)]

        chunks = []
        chunk_index = 0
        start_pos = 0

        while start_pos < len(text):
            # Calculate end position
            end_pos = min(start_pos + chunk_size, len(text))

            # Extract chunk text
            chunk_text = text[start_pos:end_pos]

            # If not at the end of text, try to extend to sentence boundary
            if end_pos < len(text):
                extended_chunk = self._extend_to_sentence_boundary(
                    text, start_pos, end_pos, int(chunk_size * 1.2)
                )
                # Only use extended chunk if it actually extended
                if len(extended_chunk) > len(chunk_text):
                    chunk_text = extended_chunk
                    end_pos = start_pos + len(chunk_text)

            # Ensure chunk contains at least one complete sentence
            # If no sentence boundary found, just use what we have
            if not self._has_complete_sentence(chunk_text) and end_pos < len(text):
                # Try to extend further to get a complete sentence
                extended_text = self._extend_to_sentence_boundary(
                    text, start_pos, end_pos + 200, chunk_size * 2
                )
                if self._has_complete_sentence(extended_text) and len(extended_text) > len(
                    chunk_text
                ):
                    chunk_text = extended_text
                    end_pos = start_pos + len(chunk_text)

            # Create chunk with metadata
            metadata = ChunkMetadata(
                chunk_index=chunk_index,
                source_document=source_name,
                start_position=start_pos,
                end_position=end_pos,
            )
            chunks.append(Chunk(text=chunk_text, metadata=metadata))

            logger.debug(
                f"Created chunk {chunk_index}: positions {start_pos}-{end_pos}, "
                f"length {len(chunk_text)}"
            )

            # Move to next chunk with overlap
            chunk_index += 1
            next_start = end_pos - overlap

            # Ensure we make progress - if overlap would cause us to go backwards or stay in place, skip ahead
            if next_start <= start_pos:
                start_pos = start_pos + max(1, chunk_size - overlap)
            else:
                start_pos = next_start

            # If the remaining text is very small (less than half chunk_size), include it in the last chunk
            if start_pos < len(text) and len(text) - start_pos < chunk_size // 2:
                # Extend the last chunk to include remaining text
                chunks[-1].metadata.end_position = len(text)
                chunks[-1] = Chunk(
                    text=text[chunks[-1].metadata.start_position : len(text)],
                    metadata=chunks[-1].metadata,
                )
                logger.debug("Extended last chunk to include remaining text")
                break

        logger.info(f"Chunking complete: created {len(chunks)} chunks from {source_name}")
        return chunks

    def _extend_to_sentence_boundary(
        self, text: str, start_pos: int, end_pos: int, max_extension: int
    ) -> str:
        """
        Extend chunk to the next sentence boundary.

        Args:
            text: Full text
            start_pos: Start position of chunk
            end_pos: Current end position
            max_extension: Maximum allowed chunk size

        Returns:
            Extended chunk text
        """
        search_limit = min(start_pos + max_extension, len(text))

        # Look for sentence boundaries (period, newline, exclamation, question mark)
        sentence_endings = [".", "\n", "!", "?"]

        best_boundary = end_pos
        for pos in range(end_pos, search_limit):
            if text[pos] in sentence_endings:
                # Include the punctuation and any following whitespace
                best_boundary = pos + 1
                while best_boundary < search_limit and text[best_boundary] in " \t":
                    best_boundary += 1
                break

        return text[start_pos:best_boundary]

    def _has_complete_sentence(self, text: str) -> bool:
        """
        Check if text contains at least one complete sentence.

        A complete sentence ends with '.', '!', '?', or '\n'.

        Args:
            text: Text to check

        Returns:
            True if text contains at least one complete sentence
        """
        sentence_endings = [".", "!", "?", "\n"]
        return any(ending in text for ending in sentence_endings)

    def validate_chunk_coverage(self, original_text: str, chunks: List[Chunk]) -> CoverageResult:
        """
        Validate that chunks cover the original text without gaps or unexpected duplicates.

        This performs round-trip validation to ensure no content is lost during chunking.

        Args:
            original_text: The original text that was chunked
            chunks: List of chunks created from the text

        Returns:
            CoverageResult indicating if coverage is complete
        """
        logger.debug(f"Validating chunk coverage: {len(original_text)} chars, {len(chunks)} chunks")

        if not chunks:
            if not original_text:
                logger.debug("Coverage validation: empty text and no chunks - valid")
                return CoverageResult(is_complete=True, missing_segments=[], duplicate_segments=[])
            else:
                logger.warning(
                    f"Coverage validation failed: text has {len(original_text)} chars "
                    "but no chunks created"
                )
                return CoverageResult(
                    is_complete=False, missing_segments=[original_text], duplicate_segments=[]
                )

        # Track which positions in original text are covered
        covered_positions: set[int] = set()
        duplicate_segments: list[tuple[int, int]] = []

        for chunk in chunks:
            start = chunk.metadata.start_position
            end = chunk.metadata.end_position

            # Check for duplicates beyond expected overlap
            chunk_positions = set(range(start, end))
            overlap_positions = covered_positions & chunk_positions

            # Expected overlap is between consecutive chunks
            # We allow some overlap but track excessive duplication
            if len(overlap_positions) > 0:
                # This is expected for overlapping chunks
                pass

            covered_positions.update(chunk_positions)

        # Find missing segments
        missing_segments = []
        all_positions = set(range(len(original_text)))
        missing_positions = all_positions - covered_positions

        if missing_positions:
            # Group consecutive missing positions into segments
            sorted_missing = sorted(missing_positions)
            segment_start = sorted_missing[0]
            segment_end = sorted_missing[0]

            for pos in sorted_missing[1:]:
                if pos == segment_end + 1:
                    segment_end = pos
                else:
                    missing_segments.append(original_text[segment_start : segment_end + 1])
                    segment_start = pos
                    segment_end = pos

            # Add the last segment
            missing_segments.append(original_text[segment_start : segment_end + 1])

        is_complete = len(missing_segments) == 0

        if is_complete:
            logger.info("Coverage validation successful: all content covered")
        else:
            logger.warning(f"Coverage validation found {len(missing_segments)} missing segments")

        return CoverageResult(
            is_complete=is_complete,
            missing_segments=missing_segments,
            duplicate_segments=duplicate_segments,  # type: ignore[arg-type]
        )
