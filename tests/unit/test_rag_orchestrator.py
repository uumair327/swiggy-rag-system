"""Unit tests for RAGOrchestrator component."""

import pytest
import numpy as np
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

from core.rag_orchestrator import RAGOrchestrator
from core.document_processor import DocumentProcessor
from core.text_chunker import TextChunker
from core.embedding_generator import EmbeddingGenerator
from core.query_handler import QueryHandler
from core.context_retriever import ContextRetriever
from core.answer_generator import AnswerGenerator
from core.models import (
    DocumentContent,
    Chunk,
    ChunkMetadata,
    Embedding,
    RetrievedChunk,
    Answer,
    IngestionResult,
    QueryResult,
    CoverageResult,
)
from ports.outbound import VectorStorePort


class TestRAGOrchestrator:
    """Test suite for RAGOrchestrator class."""

    @pytest.fixture
    def mock_document_processor(self):
        """Create a mock DocumentProcessor."""
        return Mock(spec=DocumentProcessor)

    @pytest.fixture
    def mock_text_chunker(self):
        """Create a mock TextChunker."""
        return Mock(spec=TextChunker)

    @pytest.fixture
    def mock_embedding_generator(self):
        """Create a mock EmbeddingGenerator."""
        return Mock(spec=EmbeddingGenerator)

    @pytest.fixture
    def mock_query_handler(self):
        """Create a mock QueryHandler."""
        return Mock(spec=QueryHandler)

    @pytest.fixture
    def mock_context_retriever(self):
        """Create a mock ContextRetriever."""
        return Mock(spec=ContextRetriever)

    @pytest.fixture
    def mock_answer_generator(self):
        """Create a mock AnswerGenerator."""
        return Mock(spec=AnswerGenerator)

    @pytest.fixture
    def mock_vector_store(self):
        """Create a mock VectorStorePort."""
        return Mock(spec=VectorStorePort)

    @pytest.fixture
    def orchestrator(
        self,
        mock_document_processor,
        mock_text_chunker,
        mock_embedding_generator,
        mock_query_handler,
        mock_context_retriever,
        mock_answer_generator,
        mock_vector_store,
    ):
        """Create a RAGOrchestrator with all mock dependencies."""
        return RAGOrchestrator(
            document_processor=mock_document_processor,
            text_chunker=mock_text_chunker,
            embedding_generator=mock_embedding_generator,
            query_handler=mock_query_handler,
            context_retriever=mock_context_retriever,
            answer_generator=mock_answer_generator,
            vector_store=mock_vector_store,
            index_path="./test_index.faiss",
        )

    def test_init_with_all_components(
        self,
        mock_document_processor,
        mock_text_chunker,
        mock_embedding_generator,
        mock_query_handler,
        mock_context_retriever,
        mock_answer_generator,
        mock_vector_store,
    ):
        """Test RAGOrchestrator initialization with all components."""
        orchestrator = RAGOrchestrator(
            document_processor=mock_document_processor,
            text_chunker=mock_text_chunker,
            embedding_generator=mock_embedding_generator,
            query_handler=mock_query_handler,
            context_retriever=mock_context_retriever,
            answer_generator=mock_answer_generator,
            vector_store=mock_vector_store,
            index_path="./test.faiss",
        )

        assert orchestrator.document_processor == mock_document_processor
        assert orchestrator.text_chunker == mock_text_chunker
        assert orchestrator.embedding_generator == mock_embedding_generator
        assert orchestrator.query_handler == mock_query_handler
        assert orchestrator.context_retriever == mock_context_retriever
        assert orchestrator.answer_generator == mock_answer_generator
        assert orchestrator.vector_store == mock_vector_store
        assert orchestrator.index_path == "./test.faiss"

    # Test Complete Ingestion Workflow

    def test_ingest_document_complete_workflow_success(
        self,
        orchestrator,
        mock_document_processor,
        mock_text_chunker,
        mock_embedding_generator,
        mock_vector_store,
    ):
        """Test complete ingestion workflow executes all steps successfully."""
        # Setup mock document content
        document_content = DocumentContent(
            text="This is test document content for ingestion.",
            source_path="/path/to/test.pdf",
            page_count=1,
            extraction_timestamp=datetime.now().isoformat(),
        )
        mock_document_processor.load_document.return_value = document_content

        # Setup mock chunks
        chunks = [
            Chunk(
                text="This is test document",
                metadata=ChunkMetadata(
                    chunk_index=0,
                    source_document="/path/to/test.pdf",
                    start_position=0,
                    end_position=21,
                ),
            ),
            Chunk(
                text="document content for ingestion.",
                metadata=ChunkMetadata(
                    chunk_index=1,
                    source_document="/path/to/test.pdf",
                    start_position=13,
                    end_position=44,
                ),
            ),
        ]
        mock_text_chunker.chunk_text.return_value = chunks

        # Setup mock coverage validation
        coverage_result = CoverageResult(
            is_complete=True, missing_segments=[], duplicate_segments=[]
        )
        mock_text_chunker.validate_chunk_coverage.return_value = coverage_result

        # Setup mock embeddings
        embeddings = [
            Embedding(vector=np.array([0.1, 0.2, 0.3]), source_text="This is test document"),
            Embedding(
                vector=np.array([0.4, 0.5, 0.6]), source_text="document content for ingestion."
            ),
        ]
        mock_embedding_generator.generate_embeddings_batch.return_value = embeddings

        # Setup mock vector store
        mock_vector_store.get_index_size.return_value = 2

        # Execute ingestion
        result = orchestrator.ingest_document("/path/to/test.pdf")

        # Verify result
        assert result.success is True
        assert result.chunks_created == 2
        assert result.embeddings_stored == 2
        assert result.error_message is None

        # Verify all components were called in correct order
        mock_document_processor.load_document.assert_called_once_with("/path/to/test.pdf")
        mock_text_chunker.chunk_text.assert_called_once()
        mock_text_chunker.validate_chunk_coverage.assert_called_once()
        mock_embedding_generator.generate_embeddings_batch.assert_called_once()
        mock_vector_store.add_embeddings.assert_called_once()
        mock_vector_store.save_index.assert_called_once_with("./test_index.faiss")

    def test_ingest_document_without_index_path(
        self,
        mock_document_processor,
        mock_text_chunker,
        mock_embedding_generator,
        mock_query_handler,
        mock_context_retriever,
        mock_answer_generator,
        mock_vector_store,
    ):
        """Test ingestion workflow skips persistence when no index path provided."""
        # Create orchestrator without index path
        orchestrator = RAGOrchestrator(
            document_processor=mock_document_processor,
            text_chunker=mock_text_chunker,
            embedding_generator=mock_embedding_generator,
            query_handler=mock_query_handler,
            context_retriever=mock_context_retriever,
            answer_generator=mock_answer_generator,
            vector_store=mock_vector_store,
            index_path=None,
        )

        # Setup mocks
        document_content = DocumentContent(
            text="Test content",
            source_path="/test.pdf",
            page_count=1,
            extraction_timestamp=datetime.now().isoformat(),
        )
        mock_document_processor.load_document.return_value = document_content

        chunks = [Chunk(text="Test content", metadata=ChunkMetadata(0, "/test.pdf", 0, 12))]
        mock_text_chunker.chunk_text.return_value = chunks
        mock_text_chunker.validate_chunk_coverage.return_value = CoverageResult(True, [], [])

        embeddings = [Embedding(np.array([0.1, 0.2]), "Test content")]
        mock_embedding_generator.generate_embeddings_batch.return_value = embeddings
        mock_vector_store.get_index_size.return_value = 1

        # Execute
        result = orchestrator.ingest_document("/test.pdf")

        # Verify save_index was NOT called
        mock_vector_store.save_index.assert_not_called()
        assert result.success is True

    def test_ingest_document_file_not_found_error(self, orchestrator, mock_document_processor):
        """Test ingestion handles FileNotFoundError gracefully."""
        # Setup mock to raise FileNotFoundError
        mock_document_processor.load_document.side_effect = FileNotFoundError(
            "PDF file not found at path: /nonexistent.pdf"
        )

        # Execute ingestion
        result = orchestrator.ingest_document("/nonexistent.pdf")

        # Verify error handling
        assert result.success is False
        assert result.chunks_created == 0
        assert result.embeddings_stored == 0
        assert "not found" in result.error_message

    def test_ingest_document_validation_error(self, orchestrator, mock_document_processor):
        """Test ingestion handles ValueError gracefully."""
        # Setup mock to raise ValueError
        mock_document_processor.load_document.side_effect = ValueError(
            "PDF file is corrupted or unreadable"
        )

        # Execute ingestion
        result = orchestrator.ingest_document("/corrupted.pdf")

        # Verify error handling
        assert result.success is False
        assert result.chunks_created == 0
        assert result.embeddings_stored == 0
        assert "corrupted" in result.error_message.lower()

    def test_ingest_document_unexpected_error(self, orchestrator, mock_document_processor):
        """Test ingestion handles unexpected errors gracefully."""
        # Setup mock to raise unexpected exception
        mock_document_processor.load_document.side_effect = RuntimeError("Unexpected system error")

        # Execute ingestion
        result = orchestrator.ingest_document("/test.pdf")

        # Verify error handling
        assert result.success is False
        assert result.chunks_created == 0
        assert result.embeddings_stored == 0
        assert "Unexpected error" in result.error_message

    # Test Complete Query Workflow

    def test_process_query_complete_workflow_success(
        self,
        orchestrator,
        mock_query_handler,
        mock_context_retriever,
        mock_answer_generator,
        mock_vector_store,
    ):
        """Test complete query workflow executes all steps successfully."""
        # Setup system ready
        mock_vector_store.get_index_size.return_value = 10

        # Setup mock query embedding
        query_embedding = Embedding(
            vector=np.array([0.1, 0.2, 0.3]), source_text="What is the revenue?"
        )
        mock_query_handler.process_question.return_value = query_embedding

        # Setup mock retrieved chunks
        retrieved_chunks = [
            RetrievedChunk(
                chunk=Chunk(
                    text="The revenue for 2023 was $100M.",
                    metadata=ChunkMetadata(0, "report.pdf", 0, 32),
                ),
                similarity_score=0.85,
            ),
            RetrievedChunk(
                chunk=Chunk(
                    text="Revenue increased by 20% year over year.",
                    metadata=ChunkMetadata(1, "report.pdf", 33, 74),
                ),
                similarity_score=0.72,
            ),
        ]
        mock_context_retriever.retrieve_context.return_value = retrieved_chunks

        # Setup mock answer
        answer = Answer(
            text="The revenue for 2023 was $100M, which increased by 20% year over year.",
            supporting_chunks=retrieved_chunks,
            confidence="high",
        )
        mock_answer_generator.generate_answer.return_value = answer

        # Execute query
        result = orchestrator.process_query("What is the revenue?")

        # Verify result
        assert isinstance(result, QueryResult)
        assert result.answer == answer
        assert result.processing_time_seconds > 0

        # Verify all components were called in correct order
        mock_query_handler.process_question.assert_called_once_with("What is the revenue?")
        mock_context_retriever.retrieve_context.assert_called_once()
        mock_answer_generator.generate_answer.assert_called_once_with(
            question="What is the revenue?", context=retrieved_chunks
        )

    def test_process_query_system_not_ready(self, orchestrator, mock_vector_store):
        """Test query processing when system is not ready (no embeddings)."""
        # Setup empty vector store
        mock_vector_store.get_index_size.return_value = 0

        # Execute query
        result = orchestrator.process_query("What is the revenue?")

        # Verify error response
        assert isinstance(result, QueryResult)
        assert "not initialized" in result.answer.text
        assert result.answer.confidence == "not_found"
        assert len(result.answer.supporting_chunks) == 0

    def test_process_query_validation_error(
        self, orchestrator, mock_query_handler, mock_vector_store
    ):
        """Test query processing handles validation errors gracefully."""
        # Setup system ready
        mock_vector_store.get_index_size.return_value = 10

        # Setup mock to raise ValueError
        mock_query_handler.process_question.side_effect = ValueError("Question cannot be empty")

        # Execute query
        result = orchestrator.process_query("")

        # Verify error handling
        assert isinstance(result, QueryResult)
        assert "Error:" in result.answer.text
        assert "cannot be empty" in result.answer.text
        assert result.answer.confidence == "not_found"

    def test_process_query_unexpected_error(
        self, orchestrator, mock_query_handler, mock_vector_store
    ):
        """Test query processing handles unexpected errors gracefully."""
        # Setup system ready
        mock_vector_store.get_index_size.return_value = 10

        # Setup mock to raise unexpected exception
        mock_query_handler.process_question.side_effect = RuntimeError("Unexpected embedding error")

        # Execute query
        result = orchestrator.process_query("What is the revenue?")

        # Verify error handling
        assert isinstance(result, QueryResult)
        assert "Error:" in result.answer.text
        assert result.answer.confidence == "not_found"

    def test_process_query_no_context_retrieved(
        self,
        orchestrator,
        mock_query_handler,
        mock_context_retriever,
        mock_answer_generator,
        mock_vector_store,
    ):
        """Test query processing when no relevant context is found."""
        # Setup system ready
        mock_vector_store.get_index_size.return_value = 10

        # Setup mock query embedding
        query_embedding = Embedding(
            vector=np.array([0.1, 0.2, 0.3]), source_text="What is the revenue?"
        )
        mock_query_handler.process_question.return_value = query_embedding

        # Setup empty retrieved chunks
        mock_context_retriever.retrieve_context.return_value = []

        # Setup mock answer for no context
        answer = Answer(
            text="I could not find the answer in the document.",
            supporting_chunks=[],
            confidence="not_found",
        )
        mock_answer_generator.generate_answer.return_value = answer

        # Execute query
        result = orchestrator.process_query("What is the revenue?")

        # Verify result
        assert result.answer.confidence == "not_found"
        assert len(result.answer.supporting_chunks) == 0

    # Test System Ready Validation

    def test_validate_system_ready_with_embeddings(self, orchestrator, mock_vector_store):
        """Test system ready validation returns True when embeddings exist."""
        mock_vector_store.get_index_size.return_value = 100

        result = orchestrator.validate_system_ready()

        assert result is True
        mock_vector_store.get_index_size.assert_called_once()

    def test_validate_system_ready_empty_store(self, orchestrator, mock_vector_store):
        """Test system ready validation returns False when no embeddings."""
        mock_vector_store.get_index_size.return_value = 0

        result = orchestrator.validate_system_ready()

        assert result is False

    def test_validate_system_ready_error_handling(self, orchestrator, mock_vector_store):
        """Test system ready validation handles errors gracefully."""
        mock_vector_store.get_index_size.side_effect = Exception("Store error")

        result = orchestrator.validate_system_ready()

        assert result is False

    # Test Load Index

    def test_load_index_with_provided_path(self, orchestrator, mock_vector_store):
        """Test loading index from provided path."""
        mock_vector_store.get_index_size.return_value = 50

        result = orchestrator.load_index("/custom/path/index.faiss")

        assert result is True
        mock_vector_store.load_index.assert_called_once_with("/custom/path/index.faiss")

    def test_load_index_with_default_path(self, orchestrator, mock_vector_store):
        """Test loading index from default path."""
        mock_vector_store.get_index_size.return_value = 50

        result = orchestrator.load_index()

        assert result is True
        mock_vector_store.load_index.assert_called_once_with("./test_index.faiss")

    def test_load_index_no_path_provided(
        self,
        mock_document_processor,
        mock_text_chunker,
        mock_embedding_generator,
        mock_query_handler,
        mock_context_retriever,
        mock_answer_generator,
        mock_vector_store,
    ):
        """Test loading index fails when no path is available."""
        # Create orchestrator without index path
        orchestrator = RAGOrchestrator(
            document_processor=mock_document_processor,
            text_chunker=mock_text_chunker,
            embedding_generator=mock_embedding_generator,
            query_handler=mock_query_handler,
            context_retriever=mock_context_retriever,
            answer_generator=mock_answer_generator,
            vector_store=mock_vector_store,
            index_path=None,
        )

        result = orchestrator.load_index()

        assert result is False
        mock_vector_store.load_index.assert_not_called()

    def test_load_index_file_not_found(self, orchestrator, mock_vector_store):
        """Test loading index handles FileNotFoundError."""
        mock_vector_store.load_index.side_effect = FileNotFoundError("Index file not found")

        result = orchestrator.load_index()

        assert result is False

    def test_load_index_unexpected_error(self, orchestrator, mock_vector_store):
        """Test loading index handles unexpected errors."""
        mock_vector_store.load_index.side_effect = Exception("Corrupted index")

        result = orchestrator.load_index()

        assert result is False

    # Test Error Propagation

    def test_error_propagation_from_document_processor(self, orchestrator, mock_document_processor):
        """Test that errors from DocumentProcessor are properly propagated."""
        mock_document_processor.load_document.side_effect = FileNotFoundError("File not found")

        result = orchestrator.ingest_document("/test.pdf")

        assert result.success is False
        assert "not found" in result.error_message.lower()

    def test_error_propagation_from_text_chunker(
        self, orchestrator, mock_document_processor, mock_text_chunker
    ):
        """Test that errors from TextChunker are properly propagated."""
        document_content = DocumentContent(
            text="Test",
            source_path="/test.pdf",
            page_count=1,
            extraction_timestamp=datetime.now().isoformat(),
        )
        mock_document_processor.load_document.return_value = document_content
        mock_text_chunker.chunk_text.side_effect = ValueError("Chunking error")

        result = orchestrator.ingest_document("/test.pdf")

        assert result.success is False
        assert "Chunking error" in result.error_message

    def test_error_propagation_from_embedding_generator(
        self, orchestrator, mock_document_processor, mock_text_chunker, mock_embedding_generator
    ):
        """Test that errors from EmbeddingGenerator are properly propagated."""
        document_content = DocumentContent(
            text="Test",
            source_path="/test.pdf",
            page_count=1,
            extraction_timestamp=datetime.now().isoformat(),
        )
        mock_document_processor.load_document.return_value = document_content

        chunks = [Chunk(text="Test", metadata=ChunkMetadata(0, "/test.pdf", 0, 4))]
        mock_text_chunker.chunk_text.return_value = chunks
        mock_text_chunker.validate_chunk_coverage.return_value = CoverageResult(True, [], [])

        mock_embedding_generator.generate_embeddings_batch.side_effect = RuntimeError(
            "Embedding model error"
        )

        result = orchestrator.ingest_document("/test.pdf")

        assert result.success is False
        assert "Unexpected error" in result.error_message

    def test_error_propagation_from_vector_store(
        self,
        orchestrator,
        mock_document_processor,
        mock_text_chunker,
        mock_embedding_generator,
        mock_vector_store,
    ):
        """Test that errors from VectorStore are properly propagated."""
        document_content = DocumentContent(
            text="Test",
            source_path="/test.pdf",
            page_count=1,
            extraction_timestamp=datetime.now().isoformat(),
        )
        mock_document_processor.load_document.return_value = document_content

        chunks = [Chunk(text="Test", metadata=ChunkMetadata(0, "/test.pdf", 0, 4))]
        mock_text_chunker.chunk_text.return_value = chunks
        mock_text_chunker.validate_chunk_coverage.return_value = CoverageResult(True, [], [])

        embeddings = [Embedding(np.array([0.1, 0.2]), "Test")]
        mock_embedding_generator.generate_embeddings_batch.return_value = embeddings

        mock_vector_store.add_embeddings.side_effect = RuntimeError("Storage error")

        result = orchestrator.ingest_document("/test.pdf")

        assert result.success is False
        assert "Unexpected error" in result.error_message

    def test_error_propagation_from_query_handler(
        self, orchestrator, mock_query_handler, mock_vector_store
    ):
        """Test that errors from QueryHandler are properly propagated."""
        mock_vector_store.get_index_size.return_value = 10
        mock_query_handler.process_question.side_effect = ValueError("Invalid question")

        result = orchestrator.process_query("")

        assert result.answer.confidence == "not_found"
        assert "Invalid question" in result.answer.text

    def test_error_propagation_from_context_retriever(
        self, orchestrator, mock_query_handler, mock_context_retriever, mock_vector_store
    ):
        """Test that errors from ContextRetriever are properly propagated."""
        mock_vector_store.get_index_size.return_value = 10

        query_embedding = Embedding(np.array([0.1, 0.2]), "Test query")
        mock_query_handler.process_question.return_value = query_embedding

        mock_context_retriever.retrieve_context.side_effect = RuntimeError("Retrieval error")

        result = orchestrator.process_query("Test query")

        assert result.answer.confidence == "not_found"
        assert "Error:" in result.answer.text

    def test_error_propagation_from_answer_generator(
        self,
        orchestrator,
        mock_query_handler,
        mock_context_retriever,
        mock_answer_generator,
        mock_vector_store,
    ):
        """Test that errors from AnswerGenerator are properly propagated."""
        mock_vector_store.get_index_size.return_value = 10

        query_embedding = Embedding(np.array([0.1, 0.2]), "Test query")
        mock_query_handler.process_question.return_value = query_embedding

        retrieved_chunks = [
            RetrievedChunk(
                chunk=Chunk(text="Test", metadata=ChunkMetadata(0, "test.pdf", 0, 4)),
                similarity_score=0.8,
            )
        ]
        mock_context_retriever.retrieve_context.return_value = retrieved_chunks

        mock_answer_generator.generate_answer.side_effect = RuntimeError("LLM API error")

        result = orchestrator.process_query("Test query")

        assert result.answer.confidence == "not_found"
        assert "Error:" in result.answer.text
