"""Unit tests for the factory function."""

import pytest
import os
from unittest.mock import patch, MagicMock

from core.factory import create_rag_system, validate_configuration, ConfigurationError
from core.config import RAGConfig
from core.rag_orchestrator import RAGOrchestrator


class TestValidateConfiguration:
    """Tests for configuration validation."""

    def test_valid_configuration(self):
        """Test that valid configuration passes validation."""
        config = RAGConfig(
            openai_api_key="sk-test-key",
            embedding_model_name="all-MiniLM-L6-v2",
            llm_model_name="gpt-3.5-turbo",
            chunk_size=1000,
            chunk_overlap=200,
            top_k_chunks=5,
            similarity_threshold=0.3,
            llm_temperature=0.0,
        )

        # Should not raise any exception
        validate_configuration(config)

    def test_missing_api_key(self):
        """Test that missing API key raises ConfigurationError."""
        config = RAGConfig(
            openai_api_key=None,
            embedding_model_name="all-MiniLM-L6-v2",
            llm_model_name="gpt-3.5-turbo",
        )

        with pytest.raises(ConfigurationError) as exc_info:
            validate_configuration(config)

        assert "OpenAI API key not found" in str(exc_info.value)

    def test_empty_embedding_model_name(self):
        """Test that empty embedding model name raises ConfigurationError."""
        config = RAGConfig(
            openai_api_key="sk-test-key", embedding_model_name="", llm_model_name="gpt-3.5-turbo"
        )

        with pytest.raises(ConfigurationError) as exc_info:
            validate_configuration(config)

        assert "Embedding model name cannot be empty" in str(exc_info.value)

    def test_invalid_chunk_size(self):
        """Test that invalid chunk size raises ConfigurationError."""
        config = RAGConfig(
            openai_api_key="sk-test-key",
            embedding_model_name="all-MiniLM-L6-v2",
            llm_model_name="gpt-3.5-turbo",
            chunk_size=0,
        )

        with pytest.raises(ConfigurationError) as exc_info:
            validate_configuration(config)

        assert "Chunk size must be positive" in str(exc_info.value)

    def test_chunk_overlap_greater_than_size(self):
        """Test that chunk overlap >= chunk size raises ConfigurationError."""
        config = RAGConfig(
            openai_api_key="sk-test-key",
            embedding_model_name="all-MiniLM-L6-v2",
            llm_model_name="gpt-3.5-turbo",
            chunk_size=1000,
            chunk_overlap=1000,
        )

        with pytest.raises(ConfigurationError) as exc_info:
            validate_configuration(config)

        assert "Chunk overlap" in str(exc_info.value)
        assert "must be less than" in str(exc_info.value)

    def test_invalid_similarity_threshold(self):
        """Test that invalid similarity threshold raises ConfigurationError."""
        config = RAGConfig(
            openai_api_key="sk-test-key",
            embedding_model_name="all-MiniLM-L6-v2",
            llm_model_name="gpt-3.5-turbo",
            similarity_threshold=1.5,
        )

        with pytest.raises(ConfigurationError) as exc_info:
            validate_configuration(config)

        assert "Similarity threshold must be between 0.0 and 1.0" in str(exc_info.value)


class TestCreateRAGSystem:
    """Tests for RAG system factory function."""

    @patch("core.factory.LangChainLLMAdapter")
    @patch("core.factory.FAISSAdapter")
    @patch("core.factory.SentenceTransformerAdapter")
    @patch("core.factory.PyPDFAdapter")
    def test_create_rag_system_with_valid_config(
        self, mock_pypdf, mock_sentence_transformer, mock_faiss, mock_langchain
    ):
        """Test that create_rag_system returns a RAGOrchestrator with valid config."""
        # Setup mocks
        mock_embedding_model = MagicMock()
        mock_embedding_model.get_embedding_dimension.return_value = 384
        mock_sentence_transformer.return_value = mock_embedding_model

        config = RAGConfig(
            openai_api_key="sk-test-key",
            embedding_model_name="all-MiniLM-L6-v2",
            llm_model_name="gpt-3.5-turbo",
        )

        # Create system
        orchestrator = create_rag_system(config=config)

        # Verify orchestrator is created
        assert isinstance(orchestrator, RAGOrchestrator)

        # Verify adapters were instantiated
        mock_pypdf.assert_called_once()
        mock_sentence_transformer.assert_called_once_with(model_name="all-MiniLM-L6-v2")
        mock_faiss.assert_called_once_with(dimension=384)
        mock_langchain.assert_called_once_with(
            api_key="sk-test-key", model_name="gpt-3.5-turbo", temperature=0.0
        )

    @patch.dict(
        os.environ,
        {
            "OPENAI_API_KEY": "sk-env-key",
            "EMBEDDING_MODEL": "all-mpnet-base-v2",
            "LLM_MODEL": "gpt-4",
        },
    )
    @patch("core.factory.LangChainLLMAdapter")
    @patch("core.factory.FAISSAdapter")
    @patch("core.factory.SentenceTransformerAdapter")
    @patch("core.factory.PyPDFAdapter")
    def test_create_rag_system_from_env(
        self, mock_pypdf, mock_sentence_transformer, mock_faiss, mock_langchain
    ):
        """Test that create_rag_system loads config from environment."""
        # Setup mocks
        mock_embedding_model = MagicMock()
        mock_embedding_model.get_embedding_dimension.return_value = 768
        mock_sentence_transformer.return_value = mock_embedding_model

        # Create system without config (should load from env)
        orchestrator = create_rag_system()

        # Verify orchestrator is created
        assert isinstance(orchestrator, RAGOrchestrator)

        # Verify adapters were instantiated with env values
        mock_sentence_transformer.assert_called_once_with(model_name="all-mpnet-base-v2")
        mock_langchain.assert_called_once_with(
            api_key="sk-env-key", model_name="gpt-4", temperature=0.0
        )

    def test_create_rag_system_with_invalid_config(self):
        """Test that create_rag_system raises error with invalid config."""
        config = RAGConfig(
            openai_api_key=None,  # Missing API key
            embedding_model_name="all-MiniLM-L6-v2",
            llm_model_name="gpt-3.5-turbo",
        )

        with pytest.raises(ConfigurationError):
            create_rag_system(config=config)

    @patch("core.factory.LangChainLLMAdapter")
    @patch("core.factory.FAISSAdapter")
    @patch("core.factory.SentenceTransformerAdapter")
    @patch("core.factory.PyPDFAdapter")
    def test_create_rag_system_skip_validation(
        self, mock_pypdf, mock_sentence_transformer, mock_faiss, mock_langchain
    ):
        """Test that create_rag_system can skip validation but still fails on invalid config."""
        # Setup mocks
        mock_embedding_model = MagicMock()
        mock_embedding_model.get_embedding_dimension.return_value = 384
        mock_sentence_transformer.return_value = mock_embedding_model

        # Make LangChain adapter raise error for None API key
        mock_langchain.side_effect = ValueError("API key cannot be None")

        config = RAGConfig(
            openai_api_key=None,  # Invalid config
            embedding_model_name="all-MiniLM-L6-v2",
            llm_model_name="gpt-3.5-turbo",
        )

        # Should raise error from adapter initialization even when validation is skipped
        with pytest.raises(ValueError):
            create_rag_system(config=config, validate_config=False)

    @patch("core.factory.SentenceTransformerAdapter")
    @patch("core.factory.PyPDFAdapter")
    def test_create_rag_system_adapter_initialization_failure(
        self, mock_pypdf, mock_sentence_transformer
    ):
        """Test that create_rag_system handles adapter initialization failures."""
        # Make SentenceTransformer initialization fail
        mock_sentence_transformer.side_effect = Exception("Model loading failed")

        config = RAGConfig(
            openai_api_key="sk-test-key",
            embedding_model_name="invalid-model",
            llm_model_name="gpt-3.5-turbo",
        )

        with pytest.raises(ValueError) as exc_info:
            create_rag_system(config=config)

        assert "Failed to instantiate adapters" in str(exc_info.value)
