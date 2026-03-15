"""Inbound ports define interfaces for external systems to interact with the core domain."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.models import IngestionResult, Answer


class RAGServicePort(ABC):
    """Primary entry point for RAG system operations."""

    @abstractmethod
    def ingest_document(self, file_path: str) -> "IngestionResult":
        """
        Load and index a document.

        Args:
            file_path: Path to the PDF document to ingest

        Returns:
            IngestionResult containing success status and statistics
        """

    @abstractmethod
    def ask_question(self, question: str) -> "Answer":
        """
        Process a question and return an answer.

        Args:
            question: Natural language question to answer

        Returns:
            Answer with text, supporting chunks, and confidence level
        """
