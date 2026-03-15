"""Query Handler component for the Swiggy RAG System."""

import logging

from core.embedding_generator import EmbeddingGenerator
from core.models import Embedding, ValidationResult

logger = logging.getLogger(__name__)


class QueryHandler:
    """
    Processes user questions and validates input.

    This component validates user questions and generates query embeddings
    for retrieval operations.
    """

    def __init__(self, embedding_generator: EmbeddingGenerator):
        """
        Initialize the QueryHandler.

        Args:
            embedding_generator: EmbeddingGenerator instance for query embedding
        """
        self.embedding_generator = embedding_generator
        logger.info("QueryHandler initialized")

    def validate_question(self, question: str) -> ValidationResult:
        """
        Validate that a question is not empty or whitespace-only.

        Args:
            question: User question to validate

        Returns:
            ValidationResult indicating if question is valid
        """
        if not question:
            logger.warning("Question validation failed: question is None or empty string")
            return ValidationResult(is_valid=False, error_message="Question cannot be empty.")

        if not question.strip():
            logger.warning("Question validation failed: question contains only whitespace")
            return ValidationResult(is_valid=False, error_message="Question cannot be empty.")

        logger.debug(f"Question validated successfully (length: {len(question)})")
        return ValidationResult(is_valid=True, error_message=None)

    def process_question(self, question: str) -> Embedding:
        """
        Process a question by validating and generating query embedding.

        Args:
            question: User question to process

        Returns:
            Embedding for the question

        Raises:
            ValueError: If question is invalid or embedding generation fails
        """
        # Validate question
        validation_result = self.validate_question(question)
        if not validation_result.is_valid:
            error_msg = validation_result.error_message
            logger.error(f"Question processing failed: {error_msg}")
            raise ValueError(error_msg)

        # Generate embedding for valid question
        try:
            logger.info(f"Processing question: {question[:100]}...")
            embedding = self.embedding_generator.generate_embedding(question)
            logger.info(
                f"Query embedding generated successfully " f"(dimension: {embedding.dimension})"
            )
            return embedding
        except Exception as e:
            error_msg = f"Failed to process question: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise ValueError(error_msg) from e
