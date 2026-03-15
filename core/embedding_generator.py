"""Embedding Generator component for the Swiggy RAG System."""

from typing import List
import logging

from ports.outbound import EmbeddingModelPort
from core.models import Embedding

logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """
    Generates vector embeddings for text chunks and queries.

    This component wraps the EmbeddingModelPort to provide domain-level
    embedding generation with error handling and domain model conversion.
    """

    def __init__(self, embedding_model_port: EmbeddingModelPort):
        """
        Initialize the EmbeddingGenerator.

        Args:
            embedding_model_port: Port implementation for embedding generation
        """
        self.embedding_model = embedding_model_port
        logger.info(
            f"EmbeddingGenerator initialized with embedding dimension: "
            f"{self.embedding_model.get_embedding_dimension()}"
        )

    def generate_embedding(self, text: str) -> Embedding:
        """
        Generate embedding for single text input.

        Args:
            text: Text to generate embedding for

        Returns:
            Embedding domain model with vector and source_text

        Raises:
            ValueError: If text is empty or embedding generation fails
        """
        if not text or not text.strip():
            error_msg = "Cannot generate embedding for empty text"
            logger.error(error_msg)
            raise ValueError(error_msg)

        try:
            vector = self.embedding_model.encode(text)
            logger.debug(
                f"Generated embedding for text (length: {len(text)}, "
                f"embedding dim: {len(vector)})"
            )
            return Embedding(vector=vector, source_text=text)
        except Exception as e:
            error_msg = f"Failed to generate embedding: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise ValueError(error_msg) from e

    def generate_embeddings_batch(self, texts: List[str]) -> List[Embedding]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to generate embeddings for

        Returns:
            List of Embedding domain models

        Raises:
            ValueError: If texts list is empty or embedding generation fails
        """
        if not texts:
            error_msg = "Cannot generate embeddings for empty text list"
            logger.error(error_msg)
            raise ValueError(error_msg)

        # Filter out empty texts and track their indices
        valid_texts = []
        valid_indices = []
        for i, text in enumerate(texts):
            if text and text.strip():
                valid_texts.append(text)
                valid_indices.append(i)
            else:
                logger.warning(f"Skipping empty text at index {i}")

        if not valid_texts:
            error_msg = "All texts in batch are empty"
            logger.error(error_msg)
            raise ValueError(error_msg)

        try:
            vectors = self.embedding_model.encode_batch(valid_texts)
            logger.info(
                f"Generated {len(vectors)} embeddings in batch "
                f"(embedding dim: {self.embedding_model.get_embedding_dimension()})"
            )

            # Create Embedding objects for valid texts
            embeddings = [
                Embedding(vector=vectors[i], source_text=valid_texts[i])
                for i in range(len(valid_texts))
            ]

            return embeddings
        except Exception as e:
            error_msg = f"Failed to generate batch embeddings: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise ValueError(error_msg) from e
