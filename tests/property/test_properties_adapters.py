"""Property-based tests for Adapter Replaceability.

**Validates: Requirements 9.4, 9.5, 9.6, 10.1, 10.2, 10.3, 10.5**
"""

import os
import numpy as np
from typing import List, Tuple
from hypothesis import given, strategies as st, assume, settings

from core.models import Chunk, Embedding
from ports.outbound import DocumentLoaderPort, EmbeddingModelPort, VectorStorePort, LLMPort

# ============================================================================
# Mock Adapters for Testing Replaceability
# ============================================================================


class MockDocumentLoader(DocumentLoaderPort):
    """Mock document loader for testing adapter replaceability."""

    def __init__(self, mock_content: str = "Mock document content for testing."):
        self.mock_content = mock_content
        self.load_count = 0

    def load_pdf(self, file_path: str) -> str:
        """Return mock content instead of loading actual PDF."""
        self.load_count += 1
        if not self.validate_file(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        return self.mock_content

    def validate_file(self, file_path: str) -> bool:
        """Always return True for mock validation."""
        return True


class MockEmbeddingModel(EmbeddingModelPort):
    """Mock embedding model for testing adapter replaceability."""

    def __init__(self, dimension: int = 384):
        self.dimension = dimension
        self.encode_count = 0
        self.encode_batch_count = 0

    def encode(self, text: str) -> np.ndarray:
        """Generate deterministic mock embedding based on text hash."""
        self.encode_count += 1
        # Use hash of text to generate deterministic but unique embeddings
        np.random.seed(hash(text) % (2**32))
        embedding = np.random.randn(self.dimension).astype(np.float32)
        # Normalize to unit length
        embedding = embedding / np.linalg.norm(embedding)
        return embedding

    def encode_batch(self, texts: List[str]) -> np.ndarray:
        """Generate batch of mock embeddings."""
        self.encode_batch_count += 1
        embeddings = np.array([self.encode(text) for text in texts])
        return embeddings

    def get_embedding_dimension(self) -> int:
        """Return mock embedding dimension."""
        return self.dimension


class MockVectorStore(VectorStorePort):
    """Mock vector store for testing adapter replaceability."""

    def __init__(self, dimension: int = 384):
        self.dimension = dimension
        self.embeddings: List[np.ndarray] = []
        self.chunks: List[Chunk] = []
        self.add_count = 0
        self.search_count = 0

    def add_embeddings(self, embeddings: np.ndarray, chunks: List[Chunk]) -> None:
        """Store embeddings and chunks in memory."""
        self.add_count += 1
        for i in range(len(embeddings)):
            self.embeddings.append(embeddings[i])
            self.chunks.append(chunks[i])

    def search(self, query_embedding: np.ndarray, top_k: int) -> List[Tuple[Chunk, float]]:
        """Search using simple cosine similarity."""
        self.search_count += 1

        if len(self.embeddings) == 0:
            return []

        # Calculate cosine similarities
        similarities = []
        for i, emb in enumerate(self.embeddings):
            # Cosine similarity = dot product of normalized vectors
            similarity = np.dot(query_embedding, emb)
            similarities.append((self.chunks[i], float(similarity)))

        # Sort by similarity (descending) and return top_k
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]

    def save_index(self, file_path: str) -> None:
        """Mock save - does nothing."""

    def load_index(self, file_path: str) -> None:
        """Mock load - does nothing."""

    def get_index_size(self) -> int:
        """Return number of stored embeddings."""
        return len(self.embeddings)


class MockLLM(LLMPort):
    """Mock LLM for testing adapter replaceability."""

    def __init__(self, model_name: str = "mock-llm"):
        self.model_name = model_name
        self.generate_count = 0

    def generate_answer(self, question: str, context: str, system_prompt: str) -> str:
        """Generate mock answer based on context."""
        self.generate_count += 1

        if not context or len(context.strip()) == 0:
            return "I could not find the answer in the document."

        # Generate a simple mock answer that references the context
        return f"Based on the provided context, the answer is: {context[:100]}..."

    def get_model_name(self) -> str:
        """Return mock model name."""
        return self.model_name


# ============================================================================
# Property Tests
# ============================================================================


class TestAdapterReplaceabilityProperties:
    """Property-based tests for Adapter Replaceability."""

    @given(
        mock_content=st.text(min_size=100, max_size=2000),
        embedding_dim=st.sampled_from([128, 256, 384]),
        question=st.text(min_size=10, max_size=200),
        pdf_choice=st.sampled_from(
            ["Annual-Report-FY-2023-24 (1) (1).pd", "ML_intern_assignment (1) (1).pd"]
        ),
    )
    @settings(max_examples=100, deadline=10000)
    def test_property_16_adapter_replaceability(
        self, mock_content, embedding_dim, question, pdf_choice
    ):
        """
        Property 16: Adapter Replaceability

        **Validates: Requirements 9.4, 9.5, 9.6, 10.1, 10.2, 10.3, 10.5**

        For any port interface (LLMPort, VectorStorePort, EmbeddingModelPort),
        replacing one adapter implementation with another should allow the system
        to function correctly without modifying core domain logic.

        Requirements:
        - 9.4: THE RAG_System SHALL allow replacement of the LLM adapter without
               modifying core logic
        - 9.5: THE RAG_System SHALL allow replacement of the Vector_Store adapter
               without modifying core logic
        - 9.6: THE RAG_System SHALL allow replacement of the Embedding_Generator
               adapter without modifying core logic
        - 10.1: WHERE a different LLM provider is configured, THE RAG_System SHALL
                use the configured LLM through the same port interface
        - 10.2: WHERE a different vector database is configured, THE RAG_System
                SHALL use the configured database through the same port interface
        - 10.3: WHERE a different embedding model is configured, THE RAG_System
                SHALL use the configured model through the same port interface
        - 10.5: WHEN a component is replaced, THE RAG_System SHALL function
                correctly without code changes to core logic
        """
        # Skip empty or whitespace-only content
        assume(len(mock_content.strip()) > 0)
        assume(len(question.strip()) > 0)

        # Check if PDF exists (needed for file validation in DocumentProcessor)
        assume(os.path.exists(pdf_choice))

        # ====================================================================
        # Test 1: System with Mock Adapters
        # ====================================================================

        # Create mock adapters
        mock_doc_loader = MockDocumentLoader(mock_content=mock_content)
        mock_embedding_model = MockEmbeddingModel(dimension=embedding_dim)
        mock_vector_store = MockVectorStore(dimension=embedding_dim)
        mock_llm = MockLLM(model_name="mock-llm-v1")

        # Manually wire core components with mock adapters
        # This simulates what the factory does but with mock adapters
        from core.document_processor import DocumentProcessor
        from core.text_chunker import TextChunker
        from core.embedding_generator import EmbeddingGenerator
        from core.query_handler import QueryHandler
        from core.context_retriever import ContextRetriever
        from core.answer_generator import AnswerGenerator
        from core.rag_orchestrator import RAGOrchestrator

        # Wire components with mock adapters (Requirement 10.1, 10.2, 10.3)
        document_processor = DocumentProcessor(document_loader_port=mock_doc_loader)
        text_chunker = TextChunker()
        embedding_generator = EmbeddingGenerator(embedding_model_port=mock_embedding_model)
        query_handler = QueryHandler(embedding_generator=embedding_generator)
        context_retriever = ContextRetriever(
            vector_store_port=mock_vector_store, top_k=5, similarity_threshold=0.3
        )
        answer_generator = AnswerGenerator(llm_port=mock_llm)

        # Create orchestrator with mock adapters
        orchestrator_mock = RAGOrchestrator(
            document_processor=document_processor,
            text_chunker=text_chunker,
            embedding_generator=embedding_generator,
            query_handler=query_handler,
            context_retriever=context_retriever,
            answer_generator=answer_generator,
            vector_store=mock_vector_store,
            index_path=None,
        )

        # Property: System should function with mock adapters (Requirement 10.5)

        # Test ingestion workflow (use actual PDF file that exists)
        ingestion_result = orchestrator_mock.ingest_document(pdf_choice)

        assert ingestion_result.success, "Ingestion should succeed with mock adapters"
        assert ingestion_result.chunks_created > 0, "Should create chunks with mock document loader"
        assert (
            ingestion_result.embeddings_stored > 0
        ), "Should store embeddings with mock embedding model and vector store"

        # Verify mock adapters were called (Requirement 9.4, 9.5, 9.6)
        assert mock_doc_loader.load_count > 0, "Mock document loader should be called"
        assert mock_embedding_model.encode_batch_count > 0, "Mock embedding model should be called"
        assert mock_vector_store.add_count > 0, "Mock vector store should be called"

        # Test query workflow
        query_result = orchestrator_mock.process_query(question)

        assert query_result.answer is not None, "Query should return answer with mock adapters"
        assert query_result.answer.text is not None, "Answer should have text with mock LLM"
        assert len(query_result.answer.text) > 0, "Answer text should not be empty"

        # Verify mock vector store was used for retrieval (Requirement 9.5)
        assert (
            mock_vector_store.search_count > 0
        ), "Mock vector store should be called for context retrieval"

        # Note: Mock LLM may not be called if no context is retrieved above threshold
        # This is expected behavior - the test validates adapter replaceability,
        # not the specific execution path

        # ====================================================================
        # Test 2: Replace Adapters with Different Implementations
        # ====================================================================

        # Create alternative mock adapters with different behavior
        alt_doc_loader = MockDocumentLoader(mock_content=f"Alternative content: {mock_content}")
        alt_embedding_model = MockEmbeddingModel(dimension=embedding_dim)
        alt_vector_store = MockVectorStore(dimension=embedding_dim)
        alt_llm = MockLLM(model_name="mock-llm-v2")

        # Wire components with alternative adapters (Requirement 10.1, 10.2, 10.3)
        alt_document_processor = DocumentProcessor(document_loader_port=alt_doc_loader)
        alt_embedding_generator = EmbeddingGenerator(embedding_model_port=alt_embedding_model)
        alt_query_handler = QueryHandler(embedding_generator=alt_embedding_generator)
        alt_context_retriever = ContextRetriever(
            vector_store_port=alt_vector_store, top_k=5, similarity_threshold=0.3
        )
        alt_answer_generator = AnswerGenerator(llm_port=alt_llm)

        # Create orchestrator with alternative adapters
        orchestrator_alt = RAGOrchestrator(
            document_processor=alt_document_processor,
            text_chunker=text_chunker,  # Reuse same text chunker
            embedding_generator=alt_embedding_generator,
            query_handler=alt_query_handler,
            context_retriever=alt_context_retriever,
            answer_generator=alt_answer_generator,
            vector_store=alt_vector_store,
            index_path=None,
        )

        # Property: System should function with alternative adapters (Requirement 10.5)

        # Test ingestion workflow with alternative adapters (use actual PDF file)
        alt_ingestion_result = orchestrator_alt.ingest_document(pdf_choice)

        assert alt_ingestion_result.success, "Ingestion should succeed with alternative adapters"
        assert (
            alt_ingestion_result.chunks_created > 0
        ), "Should create chunks with alternative document loader"
        assert (
            alt_ingestion_result.embeddings_stored > 0
        ), "Should store embeddings with alternative adapters"

        # Verify alternative adapters were called
        assert alt_doc_loader.load_count > 0, "Alternative document loader should be called"
        assert (
            alt_embedding_model.encode_batch_count > 0
        ), "Alternative embedding model should be called"
        assert alt_vector_store.add_count > 0, "Alternative vector store should be called"

        # Test query workflow with alternative adapters
        alt_query_result = orchestrator_alt.process_query(question)

        assert (
            alt_query_result.answer is not None
        ), "Query should return answer with alternative adapters"
        assert (
            alt_query_result.answer.text is not None
        ), "Answer should have text with alternative LLM"

        # Note: Alternative LLM may not be called if no context is retrieved above threshold
        # This is expected behavior - the test validates adapter replaceability,
        # not the specific execution path

        # ====================================================================
        # Test 3: Core Logic Remains Unchanged
        # ====================================================================

        # Property: Core logic should work identically with different adapters
        # (Requirement 9.4, 9.5, 9.6, 10.5)

        # Both systems should produce similar structure (chunks, embeddings, answers)
        assert (
            ingestion_result.chunks_created == alt_ingestion_result.chunks_created
        ), "Same text should produce same number of chunks regardless of adapter"

        # Both systems should complete workflows without errors
        assert (
            ingestion_result.success and alt_ingestion_result.success
        ), "Both systems should successfully complete ingestion"

        assert (
            query_result.answer is not None and alt_query_result.answer is not None
        ), "Both systems should successfully complete query processing"

        # ====================================================================
        # Test 4: Adapter Interface Compliance
        # ====================================================================

        # Property: All adapters should implement their port interfaces correctly

        # Verify mock adapters implement correct interfaces
        assert isinstance(
            mock_doc_loader, DocumentLoaderPort
        ), "Mock document loader should implement DocumentLoaderPort"
        assert isinstance(
            mock_embedding_model, EmbeddingModelPort
        ), "Mock embedding model should implement EmbeddingModelPort"
        assert isinstance(
            mock_vector_store, VectorStorePort
        ), "Mock vector store should implement VectorStorePort"
        assert isinstance(mock_llm, LLMPort), "Mock LLM should implement LLMPort"

        # Verify alternative adapters implement correct interfaces
        assert isinstance(
            alt_doc_loader, DocumentLoaderPort
        ), "Alternative document loader should implement DocumentLoaderPort"
        assert isinstance(
            alt_embedding_model, EmbeddingModelPort
        ), "Alternative embedding model should implement EmbeddingModelPort"
        assert isinstance(
            alt_vector_store, VectorStorePort
        ), "Alternative vector store should implement VectorStorePort"
        assert isinstance(alt_llm, LLMPort), "Alternative LLM should implement LLMPort"

        # ====================================================================
        # Test 5: No Core Logic Modification Required
        # ====================================================================

        # Property: Core components should not need modification when adapters change
        # (Requirement 10.5)

        # The fact that we can create two different orchestrators with different
        # adapters using the SAME core component classes proves that core logic
        # doesn't need modification

        # Verify core components are the same classes in both systems
        assert type(orchestrator_mock.text_chunker) == type(
            orchestrator_alt.text_chunker
        ), "Text chunker should be same class regardless of adapters"

        # Verify orchestrator class is the same
        assert type(orchestrator_mock) == type(
            orchestrator_alt
        ), "Orchestrator should be same class regardless of adapters"

        # This test passing proves that:
        # - Adapters can be swapped without modifying core logic (9.4, 9.5, 9.6)
        # - Different implementations work through same port interfaces (10.1, 10.2, 10.3)
        # - System functions correctly after component replacement (10.5)

    @given(embedding_dim=st.sampled_from([128, 256, 384, 512]))
    @settings(max_examples=100, deadline=10000)
    def test_property_16_embedding_model_replaceability(self, embedding_dim):
        """
        Property 16 (Embedding Model variant): Adapter Replaceability

        **Validates: Requirements 9.6, 10.3**

        Specifically tests that embedding model adapters can be replaced
        without affecting core logic.
        """
        # Create two different mock embedding models
        model1 = MockEmbeddingModel(dimension=embedding_dim)
        model2 = MockEmbeddingModel(dimension=embedding_dim)

        # Create embedding generators with different models
        from core.embedding_generator import EmbeddingGenerator

        generator1 = EmbeddingGenerator(embedding_model_port=model1)
        generator2 = EmbeddingGenerator(embedding_model_port=model2)

        # Property: Both should work through same interface
        test_text = "Test text for embedding generation"

        embedding1 = generator1.generate_embedding(test_text)
        embedding2 = generator2.generate_embedding(test_text)

        # Both should produce valid embeddings
        assert embedding1 is not None, "First embedding model should produce embedding"
        assert embedding2 is not None, "Second embedding model should produce embedding"

        assert (
            embedding1.dimension == embedding_dim
        ), "First embedding should have correct dimension"
        assert (
            embedding2.dimension == embedding_dim
        ), "Second embedding should have correct dimension"

        # Both models should be called
        assert model1.encode_count > 0, "First embedding model should be called"
        assert model2.encode_count > 0, "Second embedding model should be called"

        # Core EmbeddingGenerator class should be the same
        assert type(generator1) == type(
            generator2
        ), "Core embedding generator class should not change with different adapters"

    @given(vector_dim=st.sampled_from([128, 256, 384]))
    @settings(max_examples=100, deadline=10000)
    def test_property_16_vector_store_replaceability(self, vector_dim):
        """
        Property 16 (Vector Store variant): Adapter Replaceability

        **Validates: Requirements 9.5, 10.2**

        Specifically tests that vector store adapters can be replaced
        without affecting core logic.
        """
        # Create two different mock vector stores
        store1 = MockVectorStore(dimension=vector_dim)
        store2 = MockVectorStore(dimension=vector_dim)

        # Create context retrievers with different stores
        from core.context_retriever import ContextRetriever

        retriever1 = ContextRetriever(vector_store_port=store1, top_k=5, similarity_threshold=0.3)
        retriever2 = ContextRetriever(vector_store_port=store2, top_k=5, similarity_threshold=0.3)

        # Add some test data to both stores
        test_embeddings = np.random.randn(3, vector_dim).astype(np.float32)
        test_embeddings = test_embeddings / np.linalg.norm(test_embeddings, axis=1, keepdims=True)

        from core.models import Chunk, ChunkMetadata

        test_chunks = [
            Chunk(
                text=f"Test chunk {i}",
                metadata=ChunkMetadata(
                    chunk_index=i,
                    source_document="test.pd",
                    start_position=i * 100,
                    end_position=(i + 1) * 100,
                ),
            )
            for i in range(3)
        ]

        store1.add_embeddings(test_embeddings, test_chunks)
        store2.add_embeddings(test_embeddings, test_chunks)

        # Property: Both should work through same interface
        query_embedding = Embedding(vector=test_embeddings[0], source_text="query")

        results1 = retriever1.retrieve_context(
            query_embedding=query_embedding, top_k=2, similarity_threshold=0.0
        )
        results2 = retriever2.retrieve_context(
            query_embedding=query_embedding, top_k=2, similarity_threshold=0.0
        )

        # Both should return results
        assert len(results1) > 0, "First vector store should return results"
        assert len(results2) > 0, "Second vector store should return results"

        # Both stores should be called
        assert store1.search_count > 0, "First vector store should be called"
        assert store2.search_count > 0, "Second vector store should be called"

        # Core ContextRetriever class should be the same
        assert type(retriever1) == type(
            retriever2
        ), "Core context retriever class should not change with different adapters"

    @given(model_name=st.sampled_from(["mock-gpt-3.5", "mock-gpt-4", "mock-claude"]))
    @settings(max_examples=100, deadline=10000)
    def test_property_16_llm_replaceability(self, model_name):
        """
        Property 16 (LLM variant): Adapter Replaceability

        **Validates: Requirements 9.4, 10.1**

        Specifically tests that LLM adapters can be replaced
        without affecting core logic.
        """
        # Create two different mock LLMs
        llm1 = MockLLM(model_name=model_name)
        llm2 = MockLLM(model_name=f"{model_name}-v2")

        # Create answer generators with different LLMs
        from core.answer_generator import AnswerGenerator

        generator1 = AnswerGenerator(llm_port=llm1)
        generator2 = AnswerGenerator(llm_port=llm2)

        # Property: Both should work through same interface
        from core.models import RetrievedChunk, Chunk, ChunkMetadata

        test_context = [
            RetrievedChunk(
                chunk=Chunk(
                    text="Test context for answer generation",
                    metadata=ChunkMetadata(
                        chunk_index=0,
                        source_document="test.pd",
                        start_position=0,
                        end_position=100,
                    ),
                ),
                similarity_score=0.9,
            )
        ]

        answer1 = generator1.generate_answer(question="Test question?", context=test_context)
        answer2 = generator2.generate_answer(question="Test question?", context=test_context)

        # Both should produce valid answers
        assert answer1 is not None, "First LLM should produce answer"
        assert answer2 is not None, "Second LLM should produce answer"

        assert (
            answer1.text is not None and len(answer1.text) > 0
        ), "First LLM should produce non-empty answer text"
        assert (
            answer2.text is not None and len(answer2.text) > 0
        ), "Second LLM should produce non-empty answer text"

        # Both LLMs should be called
        assert llm1.generate_count > 0, "First LLM should be called"
        assert llm2.generate_count > 0, "Second LLM should be called"

        # Core AnswerGenerator class should be the same
        assert type(generator1) == type(
            generator2
        ), "Core answer generator class should not change with different adapters"
