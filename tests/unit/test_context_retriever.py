"""Unit tests for ContextRetriever component."""

import pytest
import numpy as np
from unittest.mock import Mock

from core.context_retriever import ContextRetriever
from core.models import Embedding, Chunk, ChunkMetadata, RetrievedChunk
from ports.outbound import VectorStorePort


class TestContextRetriever:
    """Test suite for ContextRetriever class."""
    
    @pytest.fixture
    def mock_vector_store(self):
        """Create a mock VectorStorePort."""
        store = Mock(spec=VectorStorePort)
        return store
    
    @pytest.fixture
    def retriever(self, mock_vector_store):
        """Create a ContextRetriever with mock vector store."""
        return ContextRetriever(
            vector_store_port=mock_vector_store,
            top_k=5,
            similarity_threshold=0.3
        )
    
    @pytest.fixture
    def sample_chunks(self):
        """Create sample chunks for testing."""
        return [
            Chunk(
                text="First chunk text",
                metadata=ChunkMetadata(0, "test.pdf", 0, 16)
            ),
            Chunk(
                text="Second chunk text",
                metadata=ChunkMetadata(1, "test.pdf", 10, 27)
            ),
            Chunk(
                text="Third chunk text",
                metadata=ChunkMetadata(2, "test.pdf", 20, 36)
            ),
        ]
    
    def test_init_with_defaults(self, mock_vector_store):
        """Test ContextRetriever initialization with default parameters."""
        retriever = ContextRetriever(mock_vector_store)
        
        assert retriever.vector_store == mock_vector_store
        assert retriever.default_top_k == 5
        assert retriever.default_similarity_threshold == 0.3
    
    def test_init_with_custom_parameters(self, mock_vector_store):
        """Test ContextRetriever initialization with custom parameters."""
        retriever = ContextRetriever(
            vector_store_port=mock_vector_store,
            top_k=10,
            similarity_threshold=0.5
        )
        
        assert retriever.default_top_k == 10
        assert retriever.default_similarity_threshold == 0.5
    
    def test_retrieve_context_top_5_chunks(self, retriever, mock_vector_store, sample_chunks):
        """Test retrieving top 5 chunks."""
        query_embedding = Embedding(
            vector=np.array([0.1, 0.2, 0.3]),
            source_text="test query"
        )
        
        # Mock vector store returns chunks with similarity scores
        mock_vector_store.search.return_value = [
            (sample_chunks[0], 0.9),
            (sample_chunks[1], 0.7),
            (sample_chunks[2], 0.5),
        ]
        
        results = retriever.retrieve_context(query_embedding)
        
        assert len(results) == 3
        assert all(isinstance(rc, RetrievedChunk) for rc in results)
        
        # Verify chunks are sorted by similarity (descending)
        assert results[0].similarity_score == 0.9
        assert results[1].similarity_score == 0.7
        assert results[2].similarity_score == 0.5
        
        mock_vector_store.search.assert_called_once_with(
            query_embedding=query_embedding.vector,
            top_k=5
        )
    
    def test_retrieve_context_similarity_threshold_filtering(self, retriever, mock_vector_store, sample_chunks):
        """Test that chunks below similarity threshold are filtered out."""
        query_embedding = Embedding(
            vector=np.array([0.1, 0.2, 0.3]),
            source_text="test query"
        )
        
        # Mock returns chunks with varying similarity scores
        mock_vector_store.search.return_value = [
            (sample_chunks[0], 0.8),  # Above threshold
            (sample_chunks[1], 0.4),  # Above threshold
            (sample_chunks[2], 0.2),  # Below threshold (0.3)
        ]
        
        results = retriever.retrieve_context(query_embedding)
        
        # Only chunks above 0.3 threshold should be returned
        assert len(results) == 2
        assert results[0].similarity_score == 0.8
        assert results[1].similarity_score == 0.4
    
    def test_retrieve_context_empty_when_no_chunks_above_threshold(self, retriever, mock_vector_store, sample_chunks):
        """Test that empty result is returned when no chunks meet threshold."""
        query_embedding = Embedding(
            vector=np.array([0.1, 0.2, 0.3]),
            source_text="test query"
        )
        
        # All chunks below threshold
        mock_vector_store.search.return_value = [
            (sample_chunks[0], 0.2),
            (sample_chunks[1], 0.1),
            (sample_chunks[2], 0.05),
        ]
        
        results = retriever.retrieve_context(query_embedding)
        
        assert len(results) == 0
    
    def test_retrieve_context_includes_chunk_text_and_metadata(self, retriever, mock_vector_store, sample_chunks):
        """Test that retrieved chunks include text and complete metadata."""
        query_embedding = Embedding(
            vector=np.array([0.1, 0.2, 0.3]),
            source_text="test query"
        )
        
        mock_vector_store.search.return_value = [
            (sample_chunks[0], 0.8),
        ]
        
        results = retriever.retrieve_context(query_embedding)
        
        assert len(results) == 1
        retrieved = results[0]
        
        # Check chunk text
        assert retrieved.chunk.text == "First chunk text"
        
        # Check complete metadata
        assert retrieved.chunk.metadata.chunk_index == 0
        assert retrieved.chunk.metadata.source_document == "test.pdf"
        assert retrieved.chunk.metadata.start_position == 0
        assert retrieved.chunk.metadata.end_position == 16
        
        # Check similarity score
        assert retrieved.similarity_score == 0.8
    
    def test_retrieve_context_custom_top_k(self, retriever, mock_vector_store, sample_chunks):
        """Test retrieving with custom top_k parameter."""
        query_embedding = Embedding(
            vector=np.array([0.1, 0.2, 0.3]),
            source_text="test query"
        )
        
        mock_vector_store.search.return_value = [
            (sample_chunks[0], 0.9),
            (sample_chunks[1], 0.8),
        ]
        
        results = retriever.retrieve_context(query_embedding, top_k=2)
        
        mock_vector_store.search.assert_called_once_with(
            query_embedding=query_embedding.vector,
            top_k=2
        )
    
    def test_retrieve_context_custom_similarity_threshold(self, retriever, mock_vector_store, sample_chunks):
        """Test retrieving with custom similarity threshold."""
        query_embedding = Embedding(
            vector=np.array([0.1, 0.2, 0.3]),
            source_text="test query"
        )
        
        mock_vector_store.search.return_value = [
            (sample_chunks[0], 0.9),
            (sample_chunks[1], 0.6),
            (sample_chunks[2], 0.4),
        ]
        
        # Use higher threshold
        results = retriever.retrieve_context(
            query_embedding,
            similarity_threshold=0.5
        )
        
        # Only chunks >= 0.5 should be returned
        assert len(results) == 2
        assert results[0].similarity_score == 0.9
        assert results[1].similarity_score == 0.6
    
    def test_retrieve_context_sorted_by_similarity(self, retriever, mock_vector_store, sample_chunks):
        """Test that results are sorted by similarity score in descending order."""
        query_embedding = Embedding(
            vector=np.array([0.1, 0.2, 0.3]),
            source_text="test query"
        )
        
        # Return chunks in non-sorted order
        mock_vector_store.search.return_value = [
            (sample_chunks[0], 0.5),
            (sample_chunks[1], 0.9),
            (sample_chunks[2], 0.7),
        ]
        
        results = retriever.retrieve_context(query_embedding)
        
        # Should be sorted descending
        assert results[0].similarity_score == 0.9
        assert results[1].similarity_score == 0.7
        assert results[2].similarity_score == 0.5
    
    def test_retrieve_context_empty_search_results(self, retriever, mock_vector_store):
        """Test handling of empty search results."""
        query_embedding = Embedding(
            vector=np.array([0.1, 0.2, 0.3]),
            source_text="test query"
        )
        
        mock_vector_store.search.return_value = []
        
        results = retriever.retrieve_context(query_embedding)
        
        assert len(results) == 0
