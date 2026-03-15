"""SentenceTransformer adapter for generating text embeddings."""

import logging
from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer

from ports.outbound import EmbeddingModelPort

logger = logging.getLogger(__name__)


class SentenceTransformerAdapter(EmbeddingModelPort):
    """
    Adapter for generating text embeddings using sentence-transformers library.

    Implements EmbeddingModelPort to provide semantic embedding generation
    using pre-trained transformer models. Returns normalized embeddings for
    consistent similarity comparisons.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the SentenceTransformer adapter.

        Args:
            model_name: Name of the sentence-transformers model to use.
                       Default is "all-MiniLM-L6-v2" (384 dimensions).
        """
        logger.info(f"SentenceTransformerAdapter: Initializing with model {model_name}")
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        self._embedding_dimension = self.model.get_sentence_embedding_dimension()
        logger.info(
            f"SentenceTransformerAdapter: Model loaded successfully, "
            f"embedding dimension: {self._embedding_dimension}"
        )

    def encode(self, text: str) -> np.ndarray:
        """
        Generate embedding for single text.

        Args:
            text: Text to encode

        Returns:
            Normalized numpy array representing the text embedding

        Raises:
            ValueError: If text is empty or encoding fails
        """
        if not text or not text.strip():
            logger.error("SentenceTransformerAdapter: Cannot encode empty text")
            raise ValueError("Cannot encode empty text")

        try:
            logger.debug(f"SentenceTransformerAdapter: Encoding text of length {len(text)}")
            # Generate embedding with normalization
            embedding = self.model.encode(text, normalize_embeddings=True, show_progress_bar=False)

            # Ensure it's a numpy array
            if not isinstance(embedding, np.ndarray):
                embedding = np.array(embedding)

            logger.debug(
                f"SentenceTransformerAdapter: Generated embedding with shape {embedding.shape}"
            )
            return embedding

        except Exception as e:
            logger.error(f"SentenceTransformerAdapter: Encoding failed: {str(e)}", exc_info=True)
            raise ValueError(f"Failed to encode text: {str(e)}") from e

    def encode_batch(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to encode

        Returns:
            Normalized numpy array of shape (len(texts), embedding_dim)

        Raises:
            ValueError: If texts list is empty or encoding fails
        """
        if not texts:
            logger.error("SentenceTransformerAdapter: Cannot encode empty text list")
            raise ValueError("Cannot encode empty text list")

        # Check for empty texts
        for i, text in enumerate(texts):
            if not text or not text.strip():
                logger.error(f"SentenceTransformerAdapter: Text at index {i} is empty")
                raise ValueError(f"Text at index {i} is empty")

        try:
            logger.info(f"SentenceTransformerAdapter: Encoding batch of {len(texts)} texts")
            # Generate embeddings in batch with normalization
            embeddings = self.model.encode(
                texts,
                normalize_embeddings=True,
                show_progress_bar=False,
                batch_size=32,  # Process in batches for efficiency
            )

            # Ensure it's a numpy array
            if not isinstance(embeddings, np.ndarray):
                embeddings = np.array(embeddings)

            logger.info(
                f"SentenceTransformerAdapter: Generated {len(embeddings)} embeddings "
                f"with shape {embeddings.shape}"
            )
            return embeddings

        except Exception as e:
            logger.error(
                f"SentenceTransformerAdapter: Batch encoding failed: {str(e)}", exc_info=True
            )
            raise ValueError(f"Failed to encode batch: {str(e)}") from e

    def get_embedding_dimension(self) -> int:
        """
        Return the dimensionality of embeddings.

        Returns:
            Integer representing embedding dimension (384 for all-MiniLM-L6-v2)
        """
        return self._embedding_dimension
