"""Unit tests for configuration management."""

import os
import pytest
from core.config import RAGConfig


class TestRAGConfig:
    """Tests for RAGConfig model."""

    def test_default_config(self):
        """Test creating RAGConfig with default values."""
        config = RAGConfig()

        assert config.chunk_size == 1000
        assert config.chunk_overlap == 200
        assert config.top_k_chunks == 5
        assert config.similarity_threshold == 0.3
        assert config.embedding_model_name == "all-MiniLM-L6-v2"
        assert config.llm_model_name == "gpt-3.5-turbo"
        assert config.llm_temperature == 0.0
        assert config.vector_index_path == "./data/vector_index.faiss"
        assert config.chunks_metadata_path == "./data/chunks_metadata.json"

    def test_custom_config(self):
        """Test creating RAGConfig with custom values."""
        config = RAGConfig(
            chunk_size=500, chunk_overlap=100, top_k_chunks=10, openai_api_key="test-key"
        )

        assert config.chunk_size == 500
        assert config.chunk_overlap == 100
        assert config.top_k_chunks == 10
        assert config.openai_api_key == "test-key"

    def test_from_env_with_defaults(self, monkeypatch):
        """Test loading config from environment with defaults."""
        # Clear any existing environment variables
        for key in ["CHUNK_SIZE", "CHUNK_OVERLAP", "OPENAI_API_KEY"]:
            monkeypatch.delenv(key, raising=False)

        config = RAGConfig.from_env()

        assert config.chunk_size == 1000
        assert config.chunk_overlap == 200
        assert config.openai_api_key is None

    def test_from_env_with_custom_values(self, monkeypatch):
        """Test loading config from environment with custom values."""
        monkeypatch.setenv("CHUNK_SIZE", "2000")
        monkeypatch.setenv("CHUNK_OVERLAP", "400")
        monkeypatch.setenv("TOP_K_CHUNKS", "10")
        monkeypatch.setenv("OPENAI_API_KEY", "test-api-key")

        config = RAGConfig.from_env()

        assert config.chunk_size == 2000
        assert config.chunk_overlap == 400
        assert config.top_k_chunks == 10
        assert config.openai_api_key == "test-api-key"
