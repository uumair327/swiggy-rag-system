"""Configuration management for the Swiggy RAG System."""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class RAGConfig:
    """System-wide configuration."""

    # Chunking parameters
    chunk_size: int = 1000
    chunk_overlap: int = 200

    # Retrieval parameters
    top_k_chunks: int = 5
    similarity_threshold: float = 0.3

    # Model configurations
    embedding_model_name: str = "all-MiniLM-L6-v2"
    llm_model_name: str = "gpt-3.5-turbo"
    llm_temperature: float = 0.0
    llm_provider: str = "openai"  # "openai" or "ollama"

    # Storage paths
    vector_index_path: str = "./data/vector_index.faiss"
    chunks_metadata_path: str = "./data/chunks_metadata.json"

    # API keys (loaded from environment)
    openai_api_key: Optional[str] = None
    ollama_base_url: str = "http://localhost:11434"

    @classmethod
    def from_env(cls) -> "RAGConfig":
        """Load configuration from environment variables."""
        return cls(
            chunk_size=int(os.getenv("CHUNK_SIZE", "1000")),
            chunk_overlap=int(os.getenv("CHUNK_OVERLAP", "200")),
            top_k_chunks=int(os.getenv("TOP_K_CHUNKS", "5")),
            similarity_threshold=float(os.getenv("SIMILARITY_THRESHOLD", "0.3")),
            embedding_model_name=os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2"),
            llm_model_name=os.getenv("LLM_MODEL", "gpt-3.5-turbo"),
            llm_temperature=float(os.getenv("LLM_TEMPERATURE", "0.0")),
            llm_provider=os.getenv("LLM_PROVIDER", "openai"),
            vector_index_path=os.getenv("VECTOR_INDEX_PATH", "./data/vector_index.faiss"),
            chunks_metadata_path=os.getenv("CHUNKS_METADATA_PATH", "./data/chunks_metadata.json"),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        )
