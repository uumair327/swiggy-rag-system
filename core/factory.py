"""Factory function for RAG system initialization with dependency injection."""

import logging
from typing import Optional

from core.config import RAGConfig
from core.rag_orchestrator import RAGOrchestrator
from core.document_processor import DocumentProcessor
from core.text_chunker import TextChunker
from core.embedding_generator import EmbeddingGenerator
from core.query_handler import QueryHandler
from core.context_retriever import ContextRetriever
from core.answer_generator import AnswerGenerator

from adapters.pypdf_adapter import PyPDFAdapter
from adapters.sentence_transformer_adapter import SentenceTransformerAdapter
from adapters.faiss_adapter import FAISSAdapter
from adapters.langchain_adapter import LangChainLLMAdapter
from adapters.ollama_adapter import OllamaAdapter

logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """Raised when required configuration is missing or invalid."""


def validate_configuration(config: RAGConfig) -> None:
    """
    Validate that all required configuration is present.

    Args:
        config: RAGConfig instance to validate

    Raises:
        ConfigurationError: If required configuration is missing or invalid
    """
    errors = []

    # Validate API key only if using OpenAI
    if config.llm_provider == "openai" and not config.openai_api_key:
        errors.append(
            "OpenAI API key not found. Set OPENAI_API_KEY environment variable "
            "or set LLM_PROVIDER=ollama to use local Ollama."
        )

    # Validate model names
    if not config.embedding_model_name:
        errors.append("Embedding model name cannot be empty")

    if not config.llm_model_name:
        errors.append("LLM model name cannot be empty")

    # Validate numeric parameters
    if config.chunk_size <= 0:
        errors.append(f"Chunk size must be positive, got {config.chunk_size}")

    if config.chunk_overlap < 0:
        errors.append(f"Chunk overlap cannot be negative, got {config.chunk_overlap}")

    if config.chunk_overlap >= config.chunk_size:
        errors.append(
            f"Chunk overlap ({config.chunk_overlap}) must be less than "
            f"chunk size ({config.chunk_size})"
        )

    if config.top_k_chunks <= 0:
        errors.append(f"Top K chunks must be positive, got {config.top_k_chunks}")

    if not 0.0 <= config.similarity_threshold <= 1.0:
        errors.append(
            "Similarity threshold must be between 0.0 and 1.0, "
            f"got {config.similarity_threshold}"
        )

    if not 0.0 <= config.llm_temperature <= 2.0:
        errors.append(
            "LLM temperature must be between 0.0 and 2.0, " f"got {config.llm_temperature}"
        )

    # Raise error if any validation failed
    if errors:
        error_message = "Configuration validation failed:\n" + "\n".join(
            f"  - {error}" for error in errors
        )
        raise ConfigurationError(error_message)

    logger.info("Configuration validation passed")


def create_rag_system(
    config: Optional[RAGConfig] = None, validate_config: bool = True
) -> RAGOrchestrator:
    """
    Create and initialize a fully configured RAG system with all dependencies.

    This factory function implements dependency injection following Hexagonal
    Architecture principles:
    1. Instantiate all adapters (external system implementations)
    2. Wire adapters to core components via constructor injection
    3. Return fully initialized RAGOrchestrator

    Args:
        config: Optional RAGConfig instance. If None, loads from environment
                using RAGConfig.from_env()
        validate_config: Whether to validate configuration before initialization

    Returns:
        Fully initialized RAGOrchestrator ready for use

    Raises:
        ConfigurationError: If required configuration is missing or invalid
        ValueError: If adapter initialization fails

    Example:
        >>> # Load configuration from environment and create system
        >>> rag_system = create_rag_system()
        >>>
        >>> # Or provide custom configuration
        >>> custom_config = RAGConfig(
        ...     embedding_model_name="all-mpnet-base-v2",
        ...     llm_model_name="gpt-4",
        ...     openai_api_key="sk-..."
        ... )
        >>> rag_system = create_rag_system(config=custom_config)
    """
    logger.info("Initializing RAG system with dependency injection...")

    # Step 1: Load configuration
    if config is None:
        logger.info("Loading configuration from environment variables...")
        config = RAGConfig.from_env()
    else:
        logger.info("Using provided configuration")

    # Step 2: Validate configuration
    if validate_config:
        logger.info("Validating configuration...")
        validate_configuration(config)

    # Step 3: Instantiate adapters (external system implementations)
    logger.info("Instantiating adapters...")

    try:
        # Document loader adapter
        logger.info("Creating PyPDF adapter...")
        document_loader = PyPDFAdapter()

        # Embedding model adapter
        logger.info(
            f"Creating SentenceTransformer adapter with model: {config.embedding_model_name}"
        )
        embedding_model = SentenceTransformerAdapter(model_name=config.embedding_model_name)

        # Get embedding dimension for vector store initialization
        embedding_dimension = embedding_model.get_embedding_dimension()
        logger.info(f"Embedding dimension: {embedding_dimension}")

        # Vector store adapter
        logger.info("Creating FAISS adapter...")
        vector_store = FAISSAdapter(dimension=embedding_dimension)

        # LLM adapter (choose based on provider)
        logger.info(f"Creating LLM adapter with provider: {config.llm_provider}")
        if config.llm_provider == "ollama":
            logger.info(f"Creating Ollama adapter with model: {config.llm_model_name}")
            llm = OllamaAdapter(
                model_name=config.llm_model_name,
                base_url=config.ollama_base_url,
                temperature=config.llm_temperature,
            )
        else:  # default to openai
            logger.info(f"Creating LangChain LLM adapter with model: {config.llm_model_name}")
            llm = LangChainLLMAdapter(
                api_key=config.openai_api_key,
                model_name=config.llm_model_name,
                temperature=config.llm_temperature,
            )

        logger.info("All adapters instantiated successfully")

    except Exception as e:
        error_msg = f"Failed to instantiate adapters: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise ValueError(error_msg) from e

    # Step 4: Wire adapters to core components via constructor injection
    logger.info("Wiring core components...")

    try:
        # Document processor (depends on document loader)
        document_processor = DocumentProcessor(document_loader_port=document_loader)

        # Text chunker (no external dependencies)
        text_chunker = TextChunker()

        # Embedding generator (depends on embedding model)
        embedding_generator = EmbeddingGenerator(embedding_model_port=embedding_model)

        # Query handler (depends on embedding generator)
        query_handler = QueryHandler(embedding_generator=embedding_generator)

        # Context retriever (depends on vector store)
        context_retriever = ContextRetriever(
            vector_store_port=vector_store,
            top_k=config.top_k_chunks,
            similarity_threshold=config.similarity_threshold,
        )

        # Answer generator (depends on LLM)
        answer_generator = AnswerGenerator(llm_port=llm)

        logger.info("Core components wired successfully")

    except Exception as e:
        error_msg = f"Failed to wire core components: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise ValueError(error_msg) from e

    # Step 5: Create and return RAG orchestrator
    logger.info("Creating RAG orchestrator...")

    try:
        orchestrator = RAGOrchestrator(
            document_processor=document_processor,
            text_chunker=text_chunker,
            embedding_generator=embedding_generator,
            query_handler=query_handler,
            context_retriever=context_retriever,
            answer_generator=answer_generator,
            vector_store=vector_store,
            index_path=config.vector_index_path,
        )

        logger.info("RAG system initialized successfully")
        logger.info("Configuration summary:")
        logger.info(f"  - Embedding model: {config.embedding_model_name}")
        logger.info(f"  - LLM model: {config.llm_model_name}")
        logger.info(f"  - Chunk size: {config.chunk_size}")
        logger.info(f"  - Chunk overlap: {config.chunk_overlap}")
        logger.info(f"  - Top K chunks: {config.top_k_chunks}")
        logger.info(f"  - Similarity threshold: {config.similarity_threshold}")
        logger.info(f"  - Vector index path: {config.vector_index_path}")

        return orchestrator

    except Exception as e:
        error_msg = f"Failed to create RAG orchestrator: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise ValueError(error_msg) from e
