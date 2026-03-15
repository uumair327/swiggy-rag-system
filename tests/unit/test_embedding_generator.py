"""Unit tests for EmbeddingGenerator component."""

import pytest
import numpy as np
from unittest.mock import Mock

from core.embedding_generator import EmbeddingGenerator
from core.models import Embedding
from ports.outbound import EmbeddingModelPort


class TestEmbeddingGenerator:
    """Test suite for EmbeddingGenerator class."""
    
    @pytest.fixture
    def mock_embedding_model(self):
        """Create a mock EmbeddingModelPort."""
        model = Mock(spec=EmbeddingModelPort)
        model.get_embedding_dimension.return_value = 384
        return model
    
    @pytest.fixture
    def generator(self, mock_embedding_model):
        """Create an EmbeddingGenerator with mock model."""
        return EmbeddingGenerator(mock_embedding_model)
    
    def test_init_with_embedding_model(self, mock_embedding_model):
        """Test EmbeddingGenerator initialization with EmbeddingModelPort."""
        generator = EmbeddingGenerator(mock_embedding_model)
        assert generator.embedding_model == mock_embedding_model
        mock_embedding_model.get_embedding_dimension.assert_called_once()
    
    def test_generate_embedding_success(self, generator, mock_embedding_model):
        """Test successful single embedding generation."""
        test_text = "This is a test sentence."
        expected_vector = np.array([0.1, 0.2, 0.3])
        
        mock_embedding_model.encode.return_value = expected_vector
        
        result = generator.generate_embedding(test_text)
        
        assert isinstance(result, Embedding)
        assert np.array_equal(result.vector, expected_vector)
        assert result.source_text == test_text
        assert result.dimension == 3
        mock_embedding_model.encode.assert_called_once_with(test_text)
    
    def test_generate_embedding_empty_text(self, generator):
        """Test that empty text raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            generator.generate_embedding("")
        
        assert "empty text" in str(exc_info.value).lower()
    
    def test_generate_embedding_whitespace_only(self, generator):
        """Test that whitespace-only text raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            generator.generate_embedding("   \n\t  ")
        
        assert "empty text" in str(exc_info.value).lower()
    
    def test_generate_embedding_model_failure(self, generator, mock_embedding_model):
        """Test handling of embedding model failures."""
        mock_embedding_model.encode.side_effect = Exception("Model error")
        
        with pytest.raises(ValueError) as exc_info:
            generator.generate_embedding("Test text")
        
        assert "Failed to generate embedding" in str(exc_info.value)
    
    def test_generate_embeddings_batch_success(self, generator, mock_embedding_model):
        """Test successful batch embedding generation."""
        test_texts = ["First text", "Second text", "Third text"]
        expected_vectors = np.array([
            [0.1, 0.2, 0.3],
            [0.4, 0.5, 0.6],
            [0.7, 0.8, 0.9]
        ])
        
        mock_embedding_model.encode_batch.return_value = expected_vectors
        mock_embedding_model.get_embedding_dimension.return_value = 3
        
        results = generator.generate_embeddings_batch(test_texts)
        
        assert len(results) == 3
        assert all(isinstance(emb, Embedding) for emb in results)
        
        for i, result in enumerate(results):
            assert np.array_equal(result.vector, expected_vectors[i])
            assert result.source_text == test_texts[i]
        
        mock_embedding_model.encode_batch.assert_called_once_with(test_texts)
    
    def test_generate_embeddings_batch_empty_list(self, generator):
        """Test that empty text list raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            generator.generate_embeddings_batch([])
        
        assert "empty text list" in str(exc_info.value).lower()
    
    def test_generate_embeddings_batch_with_empty_text(self, generator):
        """Test batch generation skips empty texts."""
        test_texts = ["Valid text", "", "Another valid text"]
        expected_vectors = np.array([
            [0.1, 0.2, 0.3],
            [0.4, 0.5, 0.6]
        ])
        
        mock_embedding_model = generator.embedding_model
        mock_embedding_model.encode_batch.return_value = expected_vectors
        mock_embedding_model.get_embedding_dimension.return_value = 3
        
        results = generator.generate_embeddings_batch(test_texts)
        
        # Should only generate embeddings for non-empty texts
        assert len(results) == 2
        assert results[0].source_text == "Valid text"
        assert results[1].source_text == "Another valid text"
    
    def test_generate_embeddings_batch_all_empty(self, generator):
        """Test that batch with all empty texts raises ValueError."""
        test_texts = ["", "  ", "\n\t"]
        
        with pytest.raises(ValueError) as exc_info:
            generator.generate_embeddings_batch(test_texts)
        
        assert "All texts in batch are empty" in str(exc_info.value)
    
    def test_generate_embeddings_batch_model_failure(self, generator, mock_embedding_model):
        """Test handling of batch embedding model failures."""
        mock_embedding_model.encode_batch.side_effect = Exception("Batch error")
        
        with pytest.raises(ValueError) as exc_info:
            generator.generate_embeddings_batch(["Text 1", "Text 2"])
        
        assert "Failed to generate batch embeddings" in str(exc_info.value)
    
    def test_embedding_is_numerical_vector(self, generator, mock_embedding_model):
        """Test that generated embedding is a numerical numpy array."""
        test_text = "Test"
        expected_vector = np.array([0.1, 0.2, 0.3, 0.4])
        
        mock_embedding_model.encode.return_value = expected_vector
        
        result = generator.generate_embedding(test_text)
        
        assert isinstance(result.vector, np.ndarray)
        assert result.vector.dtype in [np.float32, np.float64]
        assert len(result.vector) > 0
