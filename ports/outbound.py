"""Outbound ports define interfaces for the core domain to interact with external systems."""

from abc import ABC, abstractmethod
from typing import List, Tuple, TYPE_CHECKING
import numpy as np

if TYPE_CHECKING:
    from core.models import Chunk


class DocumentLoaderPort(ABC):
    """Interface for loading documents from various sources."""

    @abstractmethod
    def load_pdf(self, file_path: str) -> str:
        """
        Load PDF and extract text content.

        Args:
            file_path: Path to the PDF file

        Returns:
            Extracted text content from the PDF

        Raises:
            FileNotFoundError: If the file does not exist
            ValueError: If the file is corrupted or cannot be read
        """
        pass

    @abstractmethod
    def validate_file(self, file_path: str) -> bool:
        """
        Check if file exists and is readable.

        Args:
            file_path: Path to the file to validate

        Returns:
            True if file exists and is readable, False otherwise
        """
        pass


class EmbeddingModelPort(ABC):
    """Interface for generating text embeddings."""

    @abstractmethod
    def encode(self, text: str) -> np.ndarray:
        """
        Generate embedding for single text.

        Args:
            text: Text to encode

        Returns:
            Numpy array representing the text embedding
        """
        pass

    @abstractmethod
    def encode_batch(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to encode

        Returns:
            Numpy array of shape (len(texts), embedding_dim)
        """
        pass

    @abstractmethod
    def get_embedding_dimension(self) -> int:
        """
        Return the dimensionality of embeddings.

        Returns:
            Integer representing embedding dimension
        """
        pass


class VectorStorePort(ABC):
    """Interface for vector storage and similarity search."""

    @abstractmethod
    def add_embeddings(self, embeddings: np.ndarray, chunks: List["Chunk"]) -> None:
        """
        Store embeddings with associated chunks.

        Args:
            embeddings: Numpy array of shape (n, embedding_dim)
            chunks: List of Chunk objects corresponding to embeddings
        """
        pass

    @abstractmethod
    def search(self, query_embedding: np.ndarray, top_k: int) -> List[Tuple["Chunk", float]]:
        """
        Search for similar embeddings.

        Args:
            query_embedding: Query vector of shape (embedding_dim,)
            top_k: Number of results to return

        Returns:
            List of tuples (Chunk, similarity_score) sorted by similarity
        """
        pass

    @abstractmethod
    def save_index(self, file_path: str) -> None:
        """
        Persist index to disk.

        Args:
            file_path: Path where the index should be saved
        """
        pass

    @abstractmethod
    def load_index(self, file_path: str) -> None:
        """
        Load index from disk.

        Args:
            file_path: Path to the saved index

        Raises:
            FileNotFoundError: If the index file does not exist
        """
        pass

    @abstractmethod
    def get_index_size(self) -> int:
        """
        Return number of stored embeddings.

        Returns:
            Integer count of embeddings in the index
        """
        pass


class LLMPort(ABC):
    """Interface for Large Language Model interactions."""

    @abstractmethod
    def generate_answer(self, question: str, context: str, system_prompt: str) -> str:
        """
        Generate answer based on question and context.

        Args:
            question: User's question
            context: Retrieved context from documents
            system_prompt: System instructions for the LLM

        Returns:
            Generated answer text
        """
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """
        Return the name of the LLM being used.

        Returns:
            String identifier of the model
        """
        pass
