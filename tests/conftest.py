"""Pytest configuration and shared fixtures."""

import pytest
import os
from hypothesis import settings

# Register Hypothesis profile for property-based tests
settings.register_profile(
    "rag_system",
    max_examples=100,
    deadline=5000  # 5 seconds per test
)
settings.load_profile("rag_system")


@pytest.fixture
def sample_text():
    """Provide sample text for testing."""
    return """
    This is a sample document for testing the RAG system.
    It contains multiple sentences and paragraphs.
    
    The text should be long enough to test chunking functionality.
    We need to ensure that the system can handle various text formats.
    This includes handling punctuation, line breaks, and special characters.
    
    The document processing should preserve the structure and content.
    All information should be retrievable after indexing.
    """


@pytest.fixture
def sample_chunks():
    """Provide sample chunks for testing."""
    from core.models import Chunk, ChunkMetadata
    
    return [
        Chunk(
            text="This is the first chunk of text.",
            metadata=ChunkMetadata(
                chunk_index=0,
                source_document="test.pdf",
                start_position=0,
                end_position=33
            )
        ),
        Chunk(
            text="This is the second chunk of text.",
            metadata=ChunkMetadata(
                chunk_index=1,
                source_document="test.pdf",
                start_position=20,
                end_position=53
            )
        ),
    ]


@pytest.fixture
def rag_config():
    """Provide test configuration."""
    from core.config import RAGConfig
    
    return RAGConfig(
        chunk_size=1000,
        chunk_overlap=200,
        top_k_chunks=5,
        similarity_threshold=0.3,
        embedding_model_name="all-MiniLM-L6-v2",
        llm_model_name="gpt-3.5-turbo",
        llm_temperature=0.0,
        vector_index_path="./test_data/vector_index.faiss",
        chunks_metadata_path="./test_data/chunks_metadata.json",
        openai_api_key="test-api-key"
    )


@pytest.fixture(scope="session")
def embedding_model_cached():
    """
    Cache the embedding model for the entire test session.
    
    This fixture loads the sentence-transformers model once and reuses it
    across all integration tests to avoid repeated downloads and SSL issues.
    """
    try:
        from adapters.sentence_transformer_adapter import SentenceTransformerAdapter
        model = SentenceTransformerAdapter(model_name="all-MiniLM-L6-v2")
        return model
    except Exception as e:
        pytest.skip(f"Could not load embedding model: {e}")


@pytest.fixture
def swiggy_pdf_path():
    """Get path to Swiggy Annual Report PDF."""
    pdf_path = "Annual-Report-FY-2023-24 (1) (1).pdf"
    if not os.path.exists(pdf_path):
        pytest.skip(f"Swiggy Annual Report PDF not found at {pdf_path}")
    return pdf_path
