"""Unit tests for TextChunker component."""

import pytest
from core.text_chunker import TextChunker
from core.models import Chunk, ChunkMetadata


class TestTextChunker:
    """Test suite for TextChunker class."""

    @pytest.fixture
    def chunker(self):
        """Create a TextChunker instance."""
        return TextChunker()

    def test_chunk_text_with_default_parameters(self, chunker):
        """Test chunking with default chunk_size and overlap."""
        text = "A" * 2500  # Text longer than default chunk_size
        chunks = chunker.chunk_text(text, source_name="test.pdf")

        assert len(chunks) > 1
        assert all(isinstance(chunk, Chunk) for chunk in chunks)
        assert chunks[0].metadata.source_document == "test.pdf"

    def test_chunk_text_shorter_than_chunk_size(self, chunker):
        """Test that text shorter than chunk_size returns single chunk."""
        text = "Short text."
        chunks = chunker.chunk_text(text, chunk_size=1000, source_name="test.pdf")

        assert len(chunks) == 1
        assert chunks[0].text == text
        assert chunks[0].metadata.chunk_index == 0
        assert chunks[0].metadata.start_position == 0
        assert chunks[0].metadata.end_position == len(text)

    def test_chunk_text_with_exact_chunk_size(self, chunker):
        """Test chunking text that is exactly chunk_size."""
        text = "A" * 1000
        chunks = chunker.chunk_text(text, chunk_size=1000, overlap=200)

        assert len(chunks) == 1
        assert chunks[0].text == text

    def test_exact_1000_character_chunks(self, chunker):
        """
        Test that chunks are at most 1000 characters (or slightly more for sentence boundaries).

        Validates Requirement 2.1: Text should be split into chunks of 1000 characters.
        """
        # Create text with clear sentence boundaries
        sentence = "This is a test sentence. "
        text = sentence * 100  # 2500 characters

        chunks = chunker.chunk_text(text, chunk_size=1000, overlap=200)

        # All chunks should be close to 1000 chars
        for i, chunk in enumerate(chunks[:-1]):  # Exclude last chunk
            # Chunks may extend up to 1.2x chunk_size for sentence boundaries
            assert len(chunk.text) <= 1200, f"Chunk {i} is too long: {len(chunk.text)} chars"
            # Most chunks should be at least close to chunk_size
            assert len(chunk.text) >= 900, f"Chunk {i} is too short: {len(chunk.text)} chars"

        # Last chunk can be shorter
        if len(chunks) > 1:
            assert len(chunks[-1].text) > 0

    def test_chunk_overlap(self, chunker):
        """Test that chunks have correct overlap."""
        text = "A" * 1500
        chunks = chunker.chunk_text(text, chunk_size=1000, overlap=200)

        assert len(chunks) >= 2
        # Check that second chunk starts 800 chars after first (1000 - 200 overlap)
        if len(chunks) >= 2:
            expected_start = chunks[0].metadata.end_position - 200
            assert chunks[1].metadata.start_position == expected_start

    def test_200_character_overlap(self, chunker):
        """
        Test that consecutive chunks maintain 200 character overlap.

        Validates Requirement 2.2: Maintain an overlap of 200 characters between consecutive chunks.
        """
        # Create text with sentences to allow proper chunking
        sentence = "The quick brown fox jumps over the lazy dog. "
        text = sentence * 60  # ~2700 characters

        chunks = chunker.chunk_text(text, chunk_size=1000, overlap=200)

        assert len(chunks) >= 2, "Should create multiple chunks for this text"

        # Check overlap between consecutive chunks
        for i in range(len(chunks) - 1):
            chunk1 = chunks[i]
            chunk2 = chunks[i + 1]

            # Calculate actual overlap
            overlap_start = chunk2.metadata.start_position
            overlap_end = chunk1.metadata.end_position
            actual_overlap = overlap_end - overlap_start

            # Overlap should be approximately 200 characters
            # Allow some variance due to sentence boundary preservation
            assert (
                actual_overlap >= 150
            ), f"Overlap between chunks {i} and {i+1} is too small: {actual_overlap}"
            assert (
                actual_overlap <= 250
            ), f"Overlap between chunks {i} and {i+1} is too large: {actual_overlap}"

            # Verify the overlapping text is actually the same
            overlap_text1 = text[overlap_start:overlap_end]
            overlap_text2 = chunk2.text[: len(overlap_text1)]
            assert (
                overlap_text1 == overlap_text2
            ), f"Overlapping text doesn't match between chunks {i} and {i+1}"

    def test_sentence_boundary_preservation(self, chunker):
        """Test that chunks preserve sentence boundaries."""
        text = "This is sentence one. " * 30 + "This is sentence two. " * 30
        chunks = chunker.chunk_text(text, chunk_size=1000, overlap=200)

        # Most chunks should end with sentence boundaries
        for chunk in chunks[:-1]:  # Exclude last chunk
            # Check if chunk ends with period or extends to find one
            assert "." in chunk.text

    def test_sentence_boundary_preservation_detailed(self, chunker):
        """
        Test that chunks avoid splitting mid-sentence and preserve sentence boundaries.

        Validates Requirement 2.4: Preserve sentence boundaries to avoid splitting mid-sentence.
        Validates Requirement 2.5: Ensure the chunk contains at least one complete sentence.
        """
        # Create text with clear sentence boundaries
        sentences = [
            "The Swiggy Annual Report shows strong growth in the food delivery sector.",
            "Revenue increased by 45% year over year.",
            "The company expanded to 500 new cities during the fiscal year.",
            "Customer satisfaction ratings improved significantly.",
            "Technology investments led to better delivery times.",
        ]
        text = " ".join(sentences) * 15  # Repeat to create ~2000+ characters

        chunks = chunker.chunk_text(text, chunk_size=1000, overlap=200)

        assert len(chunks) >= 2, "Should create multiple chunks"

        # Check each chunk (except possibly the last) ends at a sentence boundary
        for i, chunk in enumerate(chunks[:-1]):
            chunk_text = chunk.text.rstrip()

            # Chunk should end with a sentence-ending punctuation
            assert chunk_text[-1] in [
                ".",
                "!",
                "?",
                "\n",
            ], f"Chunk {i} doesn't end at sentence boundary: ...{chunk_text[-50:]}"

        # Check that each chunk contains at least one complete sentence
        for i, chunk in enumerate(chunks):
            # A complete sentence should have sentence-ending punctuation
            has_complete_sentence = any(punct in chunk.text for punct in [".", "!", "?", "\n"])
            assert (
                has_complete_sentence
            ), f"Chunk {i} doesn't contain a complete sentence: {chunk.text[:100]}..."

    def test_chunk_metadata_completeness(self, chunker):
        """Test that all chunks have complete metadata."""
        text = "Test text. " * 150
        chunks = chunker.chunk_text(text, chunk_size=1000, overlap=200, source_name="doc.pdf")

        for i, chunk in enumerate(chunks):
            assert chunk.metadata.chunk_index == i
            assert chunk.metadata.source_document == "doc.pdf"
            assert chunk.metadata.start_position >= 0
            assert chunk.metadata.end_position > chunk.metadata.start_position
            assert chunk.metadata.end_position <= len(text)

    def test_empty_text(self, chunker):
        """Test chunking empty text."""
        chunks = chunker.chunk_text("", chunk_size=1000, overlap=200)
        assert len(chunks) == 0

    def test_text_with_no_sentence_boundaries(self, chunker):
        """Test chunking text without sentence boundaries."""
        text = "A" * 2500  # No periods or newlines
        chunks = chunker.chunk_text(text, chunk_size=1000, overlap=200)

        assert len(chunks) > 1
        # Should still create chunks even without sentence boundaries
        for chunk in chunks:
            assert len(chunk.text) > 0

    def test_no_sentence_boundary_handling(self, chunker):
        """
        Test fallback behavior when no sentence boundaries are found.

        Validates that the chunker handles text without sentence boundaries gracefully
        by falling back to character-based splitting.
        """
        # Create text with no sentence boundaries (no periods, exclamation marks, question marks, or newlines)
        text = "A" * 2500

        chunks = chunker.chunk_text(text, chunk_size=1000, overlap=200)

        # Should still create multiple chunks
        assert len(chunks) >= 2, "Should create multiple chunks even without sentence boundaries"

        # Chunks should still respect chunk_size limits (approximately)
        for i, chunk in enumerate(chunks[:-1]):
            # Without sentence boundaries, chunks should be close to chunk_size
            assert len(chunk.text) >= 800, f"Chunk {i} is too short: {len(chunk.text)}"
            assert len(chunk.text) <= 1200, f"Chunk {i} is too long: {len(chunk.text)}"

        # Verify overlap still exists
        if len(chunks) >= 2:
            overlap_start = chunks[1].metadata.start_position
            overlap_end = chunks[0].metadata.end_position
            actual_overlap = overlap_end - overlap_start

            # Should still have some overlap even without sentence boundaries
            assert actual_overlap > 0, "Should maintain overlap even without sentence boundaries"

        # Verify all chunks contain content
        for chunk in chunks:
            assert len(chunk.text) > 0, "All chunks should have content"

    def test_validate_chunk_coverage_complete(self, chunker):
        """Test coverage validation for complete chunking."""
        text = "This is a test. " * 80
        chunks = chunker.chunk_text(text, chunk_size=1000, overlap=200)

        coverage = chunker.validate_chunk_coverage(text, chunks)

        assert coverage.is_complete
        assert len(coverage.missing_segments) == 0

    def test_validate_chunk_coverage_with_overlap(self, chunker):
        """
        Test that validate_chunk_coverage correctly handles overlapping chunks.

        Validates that the coverage validation accounts for the 200-character overlap
        and confirms all original content is preserved.
        """
        # Create text with clear structure
        text = "Sentence number one. " * 100  # ~2100 characters

        chunks = chunker.chunk_text(text, chunk_size=1000, overlap=200)

        # Validate coverage
        coverage = chunker.validate_chunk_coverage(text, chunks)

        # Coverage should be complete
        assert coverage.is_complete, "All text should be covered by chunks"
        assert len(coverage.missing_segments) == 0, "No segments should be missing"

        # Verify that all positions in original text are covered
        covered_positions = set()
        for chunk in chunks:
            start = chunk.metadata.start_position
            end = chunk.metadata.end_position
            covered_positions.update(range(start, end))

        all_positions = set(range(len(text)))
        missing_positions = all_positions - covered_positions

        assert (
            len(missing_positions) == 0
        ), f"Missing {len(missing_positions)} positions in coverage"

    def test_validate_chunk_coverage_empty_text(self, chunker):
        """Test coverage validation for empty text."""
        coverage = chunker.validate_chunk_coverage("", [])

        assert coverage.is_complete
        assert len(coverage.missing_segments) == 0

    def test_validate_chunk_coverage_missing_chunks(self, chunker):
        """Test coverage validation detects missing content."""
        text = "This is a test document."
        # Create incomplete chunks manually
        chunks = []

        coverage = chunker.validate_chunk_coverage(text, chunks)

        assert not coverage.is_complete
        assert len(coverage.missing_segments) > 0

    def test_chunk_with_newlines(self, chunker):
        """Test chunking text with newlines as sentence boundaries."""
        text = "Line one\nLine two\nLine three\n" * 30
        chunks = chunker.chunk_text(text, chunk_size=1000, overlap=200)

        assert len(chunks) > 0
        # Chunks should respect newline boundaries
        for chunk in chunks:
            assert "\n" in chunk.text or chunk == chunks[-1]

    def test_chunk_indices_sequential(self, chunker):
        """Test that chunk indices are sequential."""
        text = "Test. " * 500
        chunks = chunker.chunk_text(text, chunk_size=1000, overlap=200)

        for i, chunk in enumerate(chunks):
            assert chunk.metadata.chunk_index == i

    def test_custom_chunk_size_and_overlap(self, chunker):
        """Test chunking with custom parameters."""
        text = "Word " * 1000
        chunks = chunker.chunk_text(text, chunk_size=500, overlap=100)

        assert len(chunks) > 1
        for chunk in chunks[:-1]:
            # Chunks should be around 500 chars (may extend for sentence boundaries)
            assert len(chunk.text) >= 500 or chunk == chunks[-1]
