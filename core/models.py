"""Core domain models for the Swiggy RAG System."""

from dataclasses import dataclass
from typing import List, Optional
import numpy as np


@dataclass
class DocumentContent:
    """Represents extracted document content."""

    text: str
    source_path: str
    page_count: int
    extraction_timestamp: str


@dataclass
class ChunkMetadata:
    """Metadata associated with a text chunk."""

    chunk_index: int
    source_document: str
    start_position: int
    end_position: int


@dataclass
class Chunk:
    """A segment of document text with metadata."""

    text: str
    metadata: ChunkMetadata


@dataclass
class Embedding:
    """Vector representation of text."""

    vector: np.ndarray
    source_text: str

    @property
    def dimension(self) -> int:
        """Return the dimensionality of the embedding vector."""
        return len(self.vector)


@dataclass
class RetrievedChunk:
    """A chunk retrieved from vector search with similarity score."""

    chunk: Chunk
    similarity_score: float


@dataclass
class Answer:
    """Generated answer with supporting evidence."""

    text: str
    supporting_chunks: List[RetrievedChunk]
    confidence: str  # "high", "medium", "low", "not_found"

    def has_answer(self) -> bool:
        """Check if an answer was found."""
        return self.confidence != "not_found"


@dataclass
class IngestionResult:
    """Result of document ingestion process."""

    success: bool
    chunks_created: int
    embeddings_stored: int
    error_message: Optional[str] = None


@dataclass
class QueryResult:
    """Result of query processing."""

    answer: Answer
    processing_time_seconds: float


@dataclass
class ValidationResult:
    """Result of validation operations."""

    is_valid: bool
    error_message: Optional[str] = None


@dataclass
class CoverageResult:
    """Result of chunk coverage validation."""

    is_complete: bool
    missing_segments: List[str]
    duplicate_segments: List[str]
