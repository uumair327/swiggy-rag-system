"""Unit tests for QueryHandler component."""

import pytest
import numpy as np
from unittest.mock import Mock

from core.query_handler import QueryHandler
from core.embedding_generator import EmbeddingGenerator
from core.models import Embedding, ValidationResult


class TestQueryHandler:
    """Test suite for QueryHandler class."""

    @pytest.fixture
    def mock_embedding_generator(self):
        """Create a mock EmbeddingGenerator."""
        generator = Mock(spec=EmbeddingGenerator)
        return generator

    @pytest.fixture
    def handler(self, mock_embedding_generator):
        """Create a QueryHandler with mock embedding generator."""
        return QueryHandler(mock_embedding_generator)

    def test_init_with_embedding_generator(self, mock_embedding_generator):
        """Test QueryHandler initialization with EmbeddingGenerator."""
        handler = QueryHandler(mock_embedding_generator)
        assert handler.embedding_generator == mock_embedding_generator

    def test_validate_question_valid(self, handler):
        """Test validation succeeds for valid question."""
        result = handler.validate_question("What is the revenue?")

        assert result.is_valid
        assert result.error_message is None

    def test_validate_question_empty_string(self, handler):
        """Test validation fails for empty string."""
        result = handler.validate_question("")

        assert not result.is_valid
        assert "cannot be empty" in result.error_message.lower()

    def test_validate_question_none(self, handler):
        """Test validation fails for None."""
        result = handler.validate_question(None)

        assert not result.is_valid
        assert "cannot be empty" in result.error_message.lower()

    def test_validate_question_whitespace_only(self, handler):
        """Test validation fails for whitespace-only question."""
        result = handler.validate_question("   \n\t  ")

        assert not result.is_valid
        assert "cannot be empty" in result.error_message.lower()

    def test_validate_question_with_leading_trailing_whitespace(self, handler):
        """Test validation succeeds for question with whitespace."""
        result = handler.validate_question("  What is the revenue?  ")

        assert result.is_valid
        assert result.error_message is None

    def test_process_question_success(self, handler, mock_embedding_generator):
        """Test successful question processing."""
        question = "What was the revenue in 2023?"
        expected_embedding = Embedding(vector=np.array([0.1, 0.2, 0.3]), source_text=question)

        mock_embedding_generator.generate_embedding.return_value = expected_embedding

        result = handler.process_question(question)

        assert isinstance(result, Embedding)
        assert result == expected_embedding
        mock_embedding_generator.generate_embedding.assert_called_once_with(question)

    def test_process_question_empty_raises_error(self, handler):
        """Test that processing empty question raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            handler.process_question("")

        assert "cannot be empty" in str(exc_info.value).lower()

    def test_process_question_whitespace_raises_error(self, handler):
        """Test that processing whitespace-only question raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            handler.process_question("   \n  ")

        assert "cannot be empty" in str(exc_info.value).lower()

    def test_process_question_embedding_failure(self, handler, mock_embedding_generator):
        """Test handling of embedding generation failure."""
        mock_embedding_generator.generate_embedding.side_effect = ValueError("Embedding error")

        with pytest.raises(ValueError) as exc_info:
            handler.process_question("Valid question")

        assert "Failed to process question" in str(exc_info.value)

    def test_process_question_generates_embedding(self, handler, mock_embedding_generator):
        """Test that valid question generates embedding."""
        question = "Test question"
        embedding = Embedding(vector=np.array([0.5, 0.6, 0.7]), source_text=question)

        mock_embedding_generator.generate_embedding.return_value = embedding

        result = handler.process_question(question)

        assert result.source_text == question
        assert isinstance(result.vector, np.ndarray)
        assert len(result.vector) > 0
