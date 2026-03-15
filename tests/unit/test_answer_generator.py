"""Unit tests for AnswerGenerator component."""

import pytest
from unittest.mock import Mock

from core.answer_generator import AnswerGenerator
from core.models import Answer, RetrievedChunk, Chunk, ChunkMetadata
from ports.outbound import LLMPort


class TestAnswerGenerator:
    """Test suite for AnswerGenerator class."""

    @pytest.fixture
    def mock_llm(self):
        """Create a mock LLMPort."""
        llm = Mock(spec=LLMPort)
        return llm

    @pytest.fixture
    def generator(self, mock_llm):
        """Create an AnswerGenerator with mock LLM."""
        return AnswerGenerator(mock_llm)

    @pytest.fixture
    def sample_context(self):
        """Create sample retrieved chunks for testing."""
        return [
            RetrievedChunk(
                chunk=Chunk(
                    text="The revenue in 2023 was $100 million.",
                    metadata=ChunkMetadata(0, "test.pdf", 0, 38),
                ),
                similarity_score=0.9,
            ),
            RetrievedChunk(
                chunk=Chunk(
                    text="The company grew by 25% year over year.",
                    metadata=ChunkMetadata(1, "test.pdf", 30, 70),
                ),
                similarity_score=0.7,
            ),
        ]

    def test_init_with_llm_port(self, mock_llm):
        """Test AnswerGenerator initialization with LLMPort."""
        generator = AnswerGenerator(mock_llm)
        assert generator.llm_port == mock_llm

    def test_generate_answer_with_sufficient_context(self, generator, mock_llm, sample_context):
        """Test answer generation with sufficient context."""
        question = "What was the revenue in 2023?"
        mock_llm.generate_answer.return_value = "The revenue in 2023 was $100 million."

        result = generator.generate_answer(question, sample_context)

        assert isinstance(result, Answer)
        assert result.text == "The revenue in 2023 was $100 million."
        assert len(result.supporting_chunks) == 2
        assert result.confidence in ["high", "medium", "low"]

        # Verify LLM was called
        mock_llm.generate_answer.assert_called_once()

    def test_generate_answer_with_insufficient_context(self, generator, mock_llm):
        """Test "not found" response with insufficient context."""
        question = "What was the revenue?"
        empty_context = []

        result = generator.generate_answer(question, empty_context)

        assert isinstance(result, Answer)
        assert result.text == generator.NOT_FOUND_RESPONSE
        assert len(result.supporting_chunks) == 0
        assert result.confidence == "not_found"

        # LLM should not be called for empty context
        mock_llm.generate_answer.assert_not_called()

    def test_generate_answer_includes_supporting_chunks(self, generator, mock_llm, sample_context):
        """Test that answer includes supporting chunks."""
        question = "What was the revenue?"
        mock_llm.generate_answer.return_value = "The revenue was $100 million."

        result = generator.generate_answer(question, sample_context)

        assert len(result.supporting_chunks) == 2
        assert result.supporting_chunks == sample_context

    def test_generate_answer_llm_returns_not_found(self, generator, mock_llm, sample_context):
        """Test handling when LLM returns not found response."""
        question = "What was the profit?"
        mock_llm.generate_answer.return_value = "I could not find the answer in the document."

        result = generator.generate_answer(question, sample_context)

        assert result.confidence == "not_found"
        assert "could not find" in result.text.lower()

    def test_validate_answer_from_context_true(self, generator, sample_context):
        """Test validation succeeds when answer references context."""
        answer = "The revenue in 2023 was $100 million according to the report."

        result = generator.validate_answer_from_context(answer, sample_context)

        assert result is True

    def test_validate_answer_from_context_false(self, generator, sample_context):
        """Test validation fails when answer doesn't reference context."""
        answer = "The profit was $50 million."  # Not in context

        result = generator.validate_answer_from_context(answer, sample_context)

        assert result is False

    def test_validate_answer_from_context_empty_context(self, generator):
        """Test validation with empty context."""
        answer = "Some answer"

        result = generator.validate_answer_from_context(answer, [])

        assert result is False

    def test_validate_answer_from_context_empty_answer(self, generator, sample_context):
        """Test validation with empty answer."""
        result = generator.validate_answer_from_context("", sample_context)

        assert result is False

    def test_answer_confidence_high(self, generator, mock_llm):
        """Test high confidence when similarity is high and answer references context."""
        context = [
            RetrievedChunk(
                chunk=Chunk(
                    text="The revenue was $100 million.",
                    metadata=ChunkMetadata(0, "test.pdf", 0, 29),
                ),
                similarity_score=0.9,
            ),
        ]

        question = "What was the revenue?"
        mock_llm.generate_answer.return_value = "The revenue was $100 million."

        result = generator.generate_answer(question, context)

        assert result.confidence == "high"

    def test_answer_confidence_medium(self, generator, mock_llm):
        """Test medium confidence when similarity is moderate."""
        context = [
            RetrievedChunk(
                chunk=Chunk(
                    text="The revenue was $100 million.",
                    metadata=ChunkMetadata(0, "test.pdf", 0, 29),
                ),
                similarity_score=0.6,
            ),
        ]

        question = "What was the revenue?"
        mock_llm.generate_answer.return_value = "The revenue was $100 million."

        result = generator.generate_answer(question, context)

        assert result.confidence == "medium"

    def test_answer_confidence_low(self, generator, mock_llm):
        """Test low confidence when answer doesn't reference context."""
        context = [
            RetrievedChunk(
                chunk=Chunk(
                    text="The revenue was $100 million.",
                    metadata=ChunkMetadata(0, "test.pdf", 0, 29),
                ),
                similarity_score=0.4,
            ),
        ]

        question = "What was the revenue?"
        mock_llm.generate_answer.return_value = "The profit was high."  # Doesn't reference context

        result = generator.generate_answer(question, context)

        assert result.confidence == "low"

    def test_anti_hallucination_prompt_used(self, generator, mock_llm, sample_context):
        """Test that anti-hallucination system prompt is used."""
        question = "What was the revenue?"
        mock_llm.generate_answer.return_value = "Answer"

        generator.generate_answer(question, sample_context)

        # Verify LLM was called with system prompt
        call_args = mock_llm.generate_answer.call_args
        assert call_args is not None
        assert "system_prompt" in call_args.kwargs or len(call_args.args) >= 3

    def test_context_text_preparation(self, generator, sample_context):
        """Test that context text is properly prepared from chunks."""
        context_text = generator._prepare_context_text(sample_context)

        assert "revenue in 2023 was $100 million" in context_text
        assert "company grew by 25%" in context_text
        assert "Similarity:" in context_text
        assert "[Chunk 1]" in context_text
        assert "[Chunk 2]" in context_text
