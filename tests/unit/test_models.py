"""Unit tests for core domain models."""

import numpy as np
from core.models import (
    DocumentContent,
    ChunkMetadata,
    Chunk,
    Embedding,
    Answer,
    ValidationResult,
)


class TestDocumentContent:
    """Tests for DocumentContent model."""

    def test_create_document_content(self):
        """Test creating a DocumentContent instance."""
        doc = DocumentContent(
            text="Sample text",
            source_path="/path/to/doc.pd",
            page_count=10,
            extraction_timestamp="2024-01-15T10:30:00",
        )

        assert doc.text == "Sample text"
        assert doc.source_path == "/path/to/doc.pd"
        assert doc.page_count == 10
        assert doc.extraction_timestamp == "2024-01-15T10:30:00"


class TestChunk:
    """Tests for Chunk and ChunkMetadata models."""

    def test_create_chunk_with_metadata(self):
        """Test creating a Chunk with metadata."""
        metadata = ChunkMetadata(
            chunk_index=0, source_document="test.pd", start_position=0, end_position=100
        )

        chunk = Chunk(text="This is a test chunk.", metadata=metadata)

        assert chunk.text == "This is a test chunk."
        assert chunk.metadata.chunk_index == 0
        assert chunk.metadata.source_document == "test.pd"
        assert chunk.metadata.start_position == 0
        assert chunk.metadata.end_position == 100


class TestEmbedding:
    """Tests for Embedding model."""

    def test_create_embedding(self):
        """Test creating an Embedding instance."""
        vector = np.array([0.1, 0.2, 0.3, 0.4])
        embedding = Embedding(vector=vector, source_text="Test text")

        assert np.array_equal(embedding.vector, vector)
        assert embedding.source_text == "Test text"
        assert embedding.dimension == 4


class TestAnswer:
    """Tests for Answer model."""

    def test_answer_has_answer_true(self):
        """Test has_answer returns True for valid answers."""
        answer = Answer(text="This is the answer", supporting_chunks=[], confidence="high")

        assert answer.has_answer() is True

    def test_answer_has_answer_false(self):
        """Test has_answer returns False for not_found."""
        answer = Answer(
            text="I could not find the answer in the document.",
            supporting_chunks=[],
            confidence="not_found",
        )

        assert answer.has_answer() is False


class TestValidationResult:
    """Tests for ValidationResult model."""

    def test_valid_result(self):
        """Test creating a valid ValidationResult."""
        result = ValidationResult(is_valid=True, error_message=None)

        assert result.is_valid is True
        assert result.error_message is None

    def test_invalid_result(self):
        """Test creating an invalid ValidationResult."""
        result = ValidationResult(is_valid=False, error_message="Validation failed")

        assert result.is_valid is False
        assert result.error_message == "Validation failed"
