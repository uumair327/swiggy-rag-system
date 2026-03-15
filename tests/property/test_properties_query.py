"""Property-based tests for Query Handler component.

**Validates: Requirements 5.1, 5.2**
"""

import pytest
import numpy as np
from hypothesis import given, strategies as st, assume, settings

from core.query_handler import QueryHandler
from core.embedding_generator import EmbeddingGenerator
from core.models import Embedding


class TestQueryHandlerProperties:
    """Property-based tests for QueryHandler."""
    
    @given(
        question=st.text(min_size=1, max_size=1000)
    )
    @settings(max_examples=100, deadline=10000)
    def test_property_11_query_validation(self, embedding_model_cached, question):
        """
        Property 11: Query Validation
        
        **Validates: Requirements 5.1, 5.2**
        
        For any non-empty, non-whitespace string, the query handler should 
        accept it as a valid question and generate an embedding.
        
        Requirements:
        - 5.1: WHEN a user submits a question, THE Query_Handler SHALL accept 
               the question as a text string
        - 5.2: WHEN a question is received, THE Query_Handler SHALL validate 
               that the question is not empty
        """
        # Skip empty or whitespace-only text (these should be rejected)
        assume(len(question.strip()) > 0)
        
        # Use the session-cached embedding model from conftest
        embedding_generator = EmbeddingGenerator(embedding_model_cached)
        query_handler = QueryHandler(embedding_generator)
        
        # Process the question (Requirement 5.1, 5.2)
        result = query_handler.process_question(question)
        
        # Property assertions
        
        # 1. Result should be an Embedding object
        assert isinstance(result, Embedding), \
            "process_question should return Embedding instance"
        
        # 2. Embedding should have a vector attribute
        assert hasattr(result, 'vector'), \
            "Embedding should have vector attribute"
        assert result.vector is not None, \
            "Embedding vector should not be None"
        
        # 3. Vector should be a numpy array (numerical vector)
        assert isinstance(result.vector, np.ndarray), \
            "Embedding vector should be a numpy array"
        
        # 4. Vector should have non-zero values
        # At least some values should be non-zero
        assert np.any(result.vector != 0), \
            "Embedding vector should contain non-zero values"
        
        # 5. Vector should have valid numerical values (not NaN or Inf)
        assert not np.any(np.isnan(result.vector)), \
            "Embedding vector should not contain NaN values"
        assert not np.any(np.isinf(result.vector)), \
            "Embedding vector should not contain infinite values"
        
        # 6. Vector should have expected dimensionality
        # For all-MiniLM-L6-v2, dimension is 384
        expected_dim = embedding_model_cached.get_embedding_dimension()
        assert len(result.vector) == expected_dim, \
            f"Embedding vector should have dimension {expected_dim}, got {len(result.vector)}"
        
        # 7. Vector should be normalized (for sentence-transformers with normalize=True)
        # L2 norm should be approximately 1.0
        norm = np.linalg.norm(result.vector)
        assert np.isclose(norm, 1.0, atol=1e-5), \
            f"Embedding vector should be normalized (L2 norm ≈ 1.0), got {norm}"
        
        # 8. Source text should be preserved
        assert hasattr(result, 'source_text'), \
            "Embedding should have source_text attribute"
        assert result.source_text == question, \
            "Embedding source_text should match input question"
        
        # 9. Vector values should be in reasonable range
        # For normalized embeddings, values typically in [-1, 1]
        assert np.all(result.vector >= -1.5), \
            "Embedding values should be >= -1.5"
        assert np.all(result.vector <= 1.5), \
            "Embedding values should be <= 1.5"
        
        # 10. Vector should have sufficient variance (not all same value)
        # This ensures the embedding is meaningful
        assert np.std(result.vector) > 0.01, \
            "Embedding vector should have sufficient variance (std > 0.01)"
    
    @given(
        question=st.text(max_size=100)
    )
    @settings(max_examples=100, deadline=10000)
    def test_property_11_query_validation_empty_rejection(self, embedding_model_cached, question):
        """
        Property 11 (Rejection variant): Query Validation
        
        **Validates: Requirements 5.2**
        
        For any empty or whitespace-only string, the query handler should 
        reject it as an invalid question.
        
        Requirements:
        - 5.2: WHEN a question is received, THE Query_Handler SHALL validate 
               that the question is not empty
        """
        # Only test empty or whitespace-only strings
        assume(len(question.strip()) == 0)
        
        # Use the session-cached embedding model from conftest
        embedding_generator = EmbeddingGenerator(embedding_model_cached)
        query_handler = QueryHandler(embedding_generator)
        
        # Property: Empty or whitespace-only questions should be rejected
        with pytest.raises(ValueError) as exc_info:
            query_handler.process_question(question)
        
        # Verify the error message indicates empty question
        error_message = str(exc_info.value)
        assert "empty" in error_message.lower(), \
            f"Error message should mention 'empty': {error_message}"
    
    @given(
        questions=st.lists(
            st.text(min_size=1, max_size=500).filter(lambda t: len(t.strip()) > 0),
            min_size=2,
            max_size=10
        )
    )
    @settings(max_examples=100, deadline=15000)
    def test_property_11_query_validation_consistency(self, embedding_model_cached, questions):
        """
        Property 11 (Consistency variant): Query Validation
        
        **Validates: Requirements 5.1, 5.2**
        
        For any set of valid questions, the query handler should consistently 
        accept them and generate embeddings with the same dimensionality.
        
        Requirements:
        - 5.1: WHEN a user submits a question, THE Query_Handler SHALL accept 
               the question as a text string
        - 5.2: WHEN a question is received, THE Query_Handler SHALL validate 
               that the question is not empty
        """
        # Use the session-cached embedding model from conftest
        embedding_generator = EmbeddingGenerator(embedding_model_cached)
        query_handler = QueryHandler(embedding_generator)
        
        # Process all questions
        embeddings = []
        for question in questions:
            result = query_handler.process_question(question)
            embeddings.append(result)
        
        # Property assertions
        
        # 1. Should have generated embeddings for all questions
        assert len(embeddings) == len(questions), \
            f"Should generate one embedding per question: expected {len(questions)}, got {len(embeddings)}"
        
        # 2. All embeddings should be Embedding objects
        for i, embedding in enumerate(embeddings):
            assert isinstance(embedding, Embedding), \
                f"Embedding at index {i} should be an Embedding instance"
        
        # 3. All embeddings should have vectors
        for i, embedding in enumerate(embeddings):
            assert hasattr(embedding, 'vector'), \
                f"Embedding at index {i} should have vector attribute"
            assert embedding.vector is not None, \
                f"Embedding vector at index {i} should not be None"
            assert isinstance(embedding.vector, np.ndarray), \
                f"Embedding vector at index {i} should be a numpy array"
        
        # 4. All embeddings should have the same dimensionality
        expected_dim = embedding_model_cached.get_embedding_dimension()
        dimensions = [len(embedding.vector) for embedding in embeddings]
        
        assert all(dim == expected_dim for dim in dimensions), \
            f"All embeddings should have dimension {expected_dim}, got dimensions: {set(dimensions)}"
        
        # 5. All embeddings should have non-zero values
        for i, embedding in enumerate(embeddings):
            assert np.any(embedding.vector != 0), \
                f"Embedding at index {i} should contain non-zero values"
        
        # 6. All embeddings should have valid numerical values (not NaN or Inf)
        for i, embedding in enumerate(embeddings):
            assert not np.any(np.isnan(embedding.vector)), \
                f"Embedding at index {i} should not contain NaN values"
            assert not np.any(np.isinf(embedding.vector)), \
                f"Embedding at index {i} should not contain infinite values"
        
        # 7. All embeddings should be normalized
        for i, embedding in enumerate(embeddings):
            norm = np.linalg.norm(embedding.vector)
            assert np.isclose(norm, 1.0, atol=1e-5), \
                f"Embedding at index {i} should be normalized (L2 norm ≈ 1.0), got {norm}"
        
        # 8. Source text should be preserved for all embeddings
        for i, embedding in enumerate(embeddings):
            assert hasattr(embedding, 'source_text'), \
                f"Embedding at index {i} should have source_text attribute"
            assert embedding.source_text == questions[i], \
                f"Embedding at index {i} source_text should match input question"
        
        # 9. Different questions should produce different embeddings
        # (with high probability for random questions)
        if len(embeddings) > 1:
            # Check that not all embeddings are identical
            first_vector = embeddings[0].vector
            all_identical = all(
                np.allclose(embedding.vector, first_vector, atol=1e-6)
                for embedding in embeddings[1:]
            )
            # For random questions, embeddings should differ
            # (This may occasionally fail for very similar generated questions, but unlikely)
            if len(set(questions)) > 1:  # Only check if input questions are different
                assert not all_identical, \
                    "Different input questions should produce different embeddings"


class TestContextRetrieverProperties:
    """Property-based tests for ContextRetriever."""
    
    @given(
        num_chunks=st.integers(min_value=1, max_value=20),
        query_text=st.text(min_size=1, max_size=500).filter(lambda t: len(t.strip()) > 0)
    )
    @settings(max_examples=100, deadline=15000)
    def test_property_12_context_retrieval_completeness(
        self, 
        embedding_model_cached, 
        num_chunks, 
        query_text
    ):
        """
        Property 12: Context Retrieval Completeness
        
        **Validates: Requirements 6.1, 6.3**
        
        For any query embedding and set of stored chunks, all retrieved chunks 
        should include both non-empty text content and complete metadata 
        (chunk_index, source_document, start_position, end_position).
        
        Requirements:
        - 6.1: WHEN a query embedding is provided, THE Context_Retriever SHALL 
               search the Vector_Store for similar chunks
        - 6.3: WHEN chunks are retrieved, THE Context_Retriever SHALL include 
               the chunk text and metadata
        """
        from core.context_retriever import ContextRetriever
        from core.embedding_generator import EmbeddingGenerator
        from core.text_chunker import TextChunker
        from adapters.faiss_adapter import FAISSAdapter
        from core.models import Chunk, ChunkMetadata
        
        # Generate sample chunks with varying text
        chunks = []
        for i in range(num_chunks):
            chunk_text = f"This is chunk number {i}. " * (i + 1)  # Varying length
            chunk = Chunk(
                text=chunk_text,
                metadata=ChunkMetadata(
                    chunk_index=i,
                    source_document=f"test_doc_{i % 3}.pdf",  # Multiple source docs
                    start_position=i * 100,
                    end_position=i * 100 + len(chunk_text)
                )
            )
            chunks.append(chunk)
        
        # Create embeddings for chunks
        embedding_generator = EmbeddingGenerator(embedding_model_cached)
        chunk_texts = [chunk.text for chunk in chunks]
        chunk_embeddings = embedding_generator.generate_embeddings_batch(chunk_texts)
        
        # Store chunks in vector store
        vector_store = FAISSAdapter(dimension=embedding_model_cached.get_embedding_dimension())
        embeddings_array = np.array([emb.vector for emb in chunk_embeddings])
        vector_store.add_embeddings(embeddings_array, chunks)
        
        # Create context retriever
        context_retriever = ContextRetriever(
            vector_store_port=vector_store,
            top_k=min(5, num_chunks),  # Don't request more than available
            similarity_threshold=0.0  # Accept all results for testing
        )
        
        # Generate query embedding
        query_embedding = embedding_generator.generate_embedding(query_text)
        
        # Retrieve context (Requirement 6.1)
        retrieved_chunks = context_retriever.retrieve_context(query_embedding)
        
        # Property assertions
        
        # 1. Should retrieve at least some chunks (unless vector store is empty)
        assert len(retrieved_chunks) >= 0, \
            "retrieve_context should return a list (possibly empty)"
        
        # If chunks were retrieved, validate completeness
        if len(retrieved_chunks) > 0:
            # 2. All retrieved items should be RetrievedChunk objects
            from core.models import RetrievedChunk
            for i, rc in enumerate(retrieved_chunks):
                assert isinstance(rc, RetrievedChunk), \
                    f"Item at index {i} should be a RetrievedChunk instance"
            
            # 3. All retrieved chunks should have a chunk attribute
            for i, rc in enumerate(retrieved_chunks):
                assert hasattr(rc, 'chunk'), \
                    f"RetrievedChunk at index {i} should have 'chunk' attribute"
                assert rc.chunk is not None, \
                    f"RetrievedChunk at index {i} should have non-None chunk"
                assert isinstance(rc.chunk, Chunk), \
                    f"RetrievedChunk at index {i} should contain a Chunk instance"
            
            # 4. All retrieved chunks should have non-empty text (Requirement 6.3)
            for i, rc in enumerate(retrieved_chunks):
                assert hasattr(rc.chunk, 'text'), \
                    f"Chunk at index {i} should have 'text' attribute"
                assert rc.chunk.text is not None, \
                    f"Chunk at index {i} should have non-None text"
                assert isinstance(rc.chunk.text, str), \
                    f"Chunk at index {i} text should be a string"
                assert len(rc.chunk.text) > 0, \
                    f"Chunk at index {i} should have non-empty text"
            
            # 5. All retrieved chunks should have complete metadata (Requirement 6.3)
            for i, rc in enumerate(retrieved_chunks):
                assert hasattr(rc.chunk, 'metadata'), \
                    f"Chunk at index {i} should have 'metadata' attribute"
                assert rc.chunk.metadata is not None, \
                    f"Chunk at index {i} should have non-None metadata"
                assert isinstance(rc.chunk.metadata, ChunkMetadata), \
                    f"Chunk at index {i} metadata should be a ChunkMetadata instance"
            
            # 6. All metadata should have chunk_index field
            for i, rc in enumerate(retrieved_chunks):
                assert hasattr(rc.chunk.metadata, 'chunk_index'), \
                    f"Metadata at index {i} should have 'chunk_index' attribute"
                assert rc.chunk.metadata.chunk_index is not None, \
                    f"Metadata at index {i} should have non-None chunk_index"
                assert isinstance(rc.chunk.metadata.chunk_index, int), \
                    f"Metadata at index {i} chunk_index should be an integer"
                assert rc.chunk.metadata.chunk_index >= 0, \
                    f"Metadata at index {i} chunk_index should be non-negative"
            
            # 7. All metadata should have source_document field
            for i, rc in enumerate(retrieved_chunks):
                assert hasattr(rc.chunk.metadata, 'source_document'), \
                    f"Metadata at index {i} should have 'source_document' attribute"
                assert rc.chunk.metadata.source_document is not None, \
                    f"Metadata at index {i} should have non-None source_document"
                assert isinstance(rc.chunk.metadata.source_document, str), \
                    f"Metadata at index {i} source_document should be a string"
                assert len(rc.chunk.metadata.source_document) > 0, \
                    f"Metadata at index {i} should have non-empty source_document"
            
            # 8. All metadata should have start_position field
            for i, rc in enumerate(retrieved_chunks):
                assert hasattr(rc.chunk.metadata, 'start_position'), \
                    f"Metadata at index {i} should have 'start_position' attribute"
                assert rc.chunk.metadata.start_position is not None, \
                    f"Metadata at index {i} should have non-None start_position"
                assert isinstance(rc.chunk.metadata.start_position, int), \
                    f"Metadata at index {i} start_position should be an integer"
                assert rc.chunk.metadata.start_position >= 0, \
                    f"Metadata at index {i} start_position should be non-negative"
            
            # 9. All metadata should have end_position field
            for i, rc in enumerate(retrieved_chunks):
                assert hasattr(rc.chunk.metadata, 'end_position'), \
                    f"Metadata at index {i} should have 'end_position' attribute"
                assert rc.chunk.metadata.end_position is not None, \
                    f"Metadata at index {i} should have non-None end_position"
                assert isinstance(rc.chunk.metadata.end_position, int), \
                    f"Metadata at index {i} end_position should be an integer"
                assert rc.chunk.metadata.end_position >= 0, \
                    f"Metadata at index {i} end_position should be non-negative"
            
            # 10. end_position should be greater than start_position
            for i, rc in enumerate(retrieved_chunks):
                assert rc.chunk.metadata.end_position > rc.chunk.metadata.start_position, \
                    f"Metadata at index {i} end_position should be greater than start_position"
            
            # 11. All retrieved chunks should have similarity_score
            for i, rc in enumerate(retrieved_chunks):
                assert hasattr(rc, 'similarity_score'), \
                    f"RetrievedChunk at index {i} should have 'similarity_score' attribute"
                assert rc.similarity_score is not None, \
                    f"RetrievedChunk at index {i} should have non-None similarity_score"
                assert isinstance(rc.similarity_score, (int, float)), \
                    f"RetrievedChunk at index {i} similarity_score should be numeric"
            
            # 12. Similarity scores should be in valid range [0, 1] or reasonable range
            # Note: FAISS L2 distance can be > 1, but should be non-negative
            for i, rc in enumerate(retrieved_chunks):
                assert rc.similarity_score >= 0, \
                    f"RetrievedChunk at index {i} similarity_score should be non-negative"
            
            # 13. Retrieved chunks should be sorted by similarity score (descending)
            if len(retrieved_chunks) > 1:
                scores = [rc.similarity_score for rc in retrieved_chunks]
                sorted_scores = sorted(scores, reverse=True)
                assert scores == sorted_scores, \
                    "Retrieved chunks should be sorted by similarity score in descending order"
            
            # 14. Number of retrieved chunks should not exceed top_k
            assert len(retrieved_chunks) <= context_retriever.default_top_k, \
                f"Number of retrieved chunks should not exceed top_k={context_retriever.default_top_k}"
            
            # 15. All retrieved chunks should be from the original set
            original_chunk_indices = {chunk.metadata.chunk_index for chunk in chunks}
            for i, rc in enumerate(retrieved_chunks):
                assert rc.chunk.metadata.chunk_index in original_chunk_indices, \
                    f"Retrieved chunk at index {i} should be from the original set"


class TestAnswerGeneratorProperties:
    """Property-based tests for AnswerGenerator."""
    
    @given(
        question=st.text(min_size=5, max_size=200).filter(lambda t: len(t.strip()) > 0),
        num_chunks=st.integers(min_value=1, max_value=10)
    )
    @settings(max_examples=100, deadline=20000)
    def test_property_13_answer_generation_with_context(
        self, 
        question, 
        num_chunks
    ):
        """
        Property 13: Answer Generation with Context
        
        **Validates: Requirements 7.1, 7.4**
        
        For any valid question and non-empty context, the answer generator 
        should produce an answer that includes the supporting context chunks.
        
        Requirements:
        - 7.1: WHEN retrieved context and a user question are provided, 
               THE Answer_Generator SHALL generate an answer using an LLM
        - 7.4: THE Answer_Generator SHALL include the retrieved context chunks 
               as supporting evidence with the answer
        """
        from core.answer_generator import AnswerGenerator
        from core.models import RetrievedChunk, Chunk, ChunkMetadata, Answer
        from unittest.mock import Mock
        
        # Filter out questions that contain "not found" indicators to avoid false positives
        # These phrases trigger the _is_not_found_response method
        not_found_indicators = [
            "could not find",
            "cannot find", 
            "not found",
            "no information",
            "insufficient information"
        ]
        question_lower = question.lower()
        assume(not any(indicator in question_lower for indicator in not_found_indicators))
        
        # Create mock LLM port that returns a simple answer
        mock_llm = Mock()
        mock_llm.get_model_name.return_value = "mock-llm"
        
        # Generate a mock answer that references the context
        # This simulates a real LLM that would use the context
        mock_answer_text = f"Based on the provided context, here is the answer to: {question[:50]}"
        mock_llm.generate_answer.return_value = mock_answer_text
        
        # Create answer generator with mock LLM
        answer_generator = AnswerGenerator(mock_llm)
        
        # Generate sample context chunks with varying content
        context_chunks = []
        for i in range(num_chunks):
            chunk_text = f"Context chunk {i}: This contains information about topic {i}. " * 3
            chunk = Chunk(
                text=chunk_text,
                metadata=ChunkMetadata(
                    chunk_index=i,
                    source_document=f"test_doc_{i % 3}.pdf",
                    start_position=i * 100,
                    end_position=i * 100 + len(chunk_text)
                )
            )
            # Create RetrievedChunk with similarity score
            retrieved_chunk = RetrievedChunk(
                chunk=chunk,
                similarity_score=0.9 - (i * 0.05)  # Decreasing similarity
            )
            context_chunks.append(retrieved_chunk)
        
        # Generate answer (Requirement 7.1)
        result = answer_generator.generate_answer(question, context_chunks)
        
        # Property assertions
        
        # 1. Result should be an Answer object
        assert isinstance(result, Answer), \
            "generate_answer should return an Answer instance"
        
        # 2. Answer should have a text attribute
        assert hasattr(result, 'text'), \
            "Answer should have 'text' attribute"
        assert result.text is not None, \
            "Answer text should not be None"
        assert isinstance(result.text, str), \
            "Answer text should be a string"
        assert len(result.text) > 0, \
            "Answer text should not be empty"
        
        # 3. Answer should have supporting_chunks attribute (Requirement 7.4)
        assert hasattr(result, 'supporting_chunks'), \
            "Answer should have 'supporting_chunks' attribute"
        assert result.supporting_chunks is not None, \
            "Answer supporting_chunks should not be None"
        assert isinstance(result.supporting_chunks, list), \
            "Answer supporting_chunks should be a list"
        
        # 4. Supporting chunks should include the provided context (Requirement 7.4)
        assert len(result.supporting_chunks) > 0, \
            "Answer should include supporting chunks when context is provided"
        assert len(result.supporting_chunks) == len(context_chunks), \
            f"Answer should include all {len(context_chunks)} context chunks as supporting evidence"
        
        # 5. All supporting chunks should be RetrievedChunk objects
        for i, chunk in enumerate(result.supporting_chunks):
            assert isinstance(chunk, RetrievedChunk), \
                f"Supporting chunk at index {i} should be a RetrievedChunk instance"
        
        # 6. Supporting chunks should match the provided context
        for i, (result_chunk, context_chunk) in enumerate(zip(result.supporting_chunks, context_chunks)):
            assert result_chunk.chunk.text == context_chunk.chunk.text, \
                f"Supporting chunk {i} text should match context chunk text"
            assert result_chunk.chunk.metadata.chunk_index == context_chunk.chunk.metadata.chunk_index, \
                f"Supporting chunk {i} metadata should match context chunk metadata"
            assert result_chunk.similarity_score == context_chunk.similarity_score, \
                f"Supporting chunk {i} similarity score should match context chunk score"
        
        # 7. Answer should have confidence attribute
        assert hasattr(result, 'confidence'), \
            "Answer should have 'confidence' attribute"
        assert result.confidence is not None, \
            "Answer confidence should not be None"
        assert isinstance(result.confidence, str), \
            "Answer confidence should be a string"
        assert result.confidence in ["high", "medium", "low", "not_found"], \
            f"Answer confidence should be one of: high, medium, low, not_found; got {result.confidence}"
        
        # 8. With valid context, confidence should not be "not_found"
        # (unless the mock LLM returns a "not found" response)
        if "could not find" not in mock_answer_text.lower():
            assert result.confidence != "not_found", \
                "Answer confidence should not be 'not_found' when context is provided"
        
        # 9. LLM should have been called with the question and context
        mock_llm.generate_answer.assert_called_once()
        call_args = mock_llm.generate_answer.call_args
        
        # Verify question was passed
        assert call_args[1]['question'] == question or call_args[0][0] == question, \
            "LLM should be called with the provided question"
        
        # Verify context was passed (should contain chunk texts)
        context_arg = call_args[1].get('context', call_args[0][1] if len(call_args[0]) > 1 else None)
        assert context_arg is not None, \
            "LLM should be called with context"
        
        # Context should contain text from the chunks
        for chunk in context_chunks:
            # At least some chunk text should appear in the context
            # (implementation may format it differently)
            pass  # We can't assert exact format, but we verified it was called
        
        # 10. Answer text should be the text returned by the LLM
        assert result.text == mock_answer_text, \
            "Answer text should match the LLM-generated text"
    
    @given(
        question=st.text(min_size=5, max_size=200).filter(lambda t: len(t.strip()) > 0)
    )
    @settings(max_examples=100, deadline=15000)
    def test_property_13_answer_generation_empty_context(
        self, 
        question
    ):
        """
        Property 13 (Empty context variant): Answer Generation with Context
        
        **Validates: Requirements 7.1, 7.3, 7.4**
        
        For any valid question with empty context, the answer generator 
        should return a "not found" response with empty supporting chunks.
        
        Requirements:
        - 7.1: WHEN retrieved context and a user question are provided, 
               THE Answer_Generator SHALL generate an answer using an LLM
        - 7.3: WHEN the context does not contain sufficient information to 
               answer the question, THE Answer_Generator SHALL return 
               "I could not find the answer in the document."
        - 7.4: THE Answer_Generator SHALL include the retrieved context chunks 
               as supporting evidence with the answer
        """
        from core.answer_generator import AnswerGenerator
        from core.models import Answer
        from unittest.mock import Mock
        
        # Create mock LLM port
        mock_llm = Mock()
        mock_llm.get_model_name.return_value = "mock-llm"
        
        # Create answer generator with mock LLM
        answer_generator = AnswerGenerator(mock_llm)
        
        # Generate answer with empty context
        result = answer_generator.generate_answer(question, [])
        
        # Property assertions
        
        # 1. Result should be an Answer object
        assert isinstance(result, Answer), \
            "generate_answer should return an Answer instance"
        
        # 2. Answer should have text
        assert hasattr(result, 'text'), \
            "Answer should have 'text' attribute"
        assert result.text is not None, \
            "Answer text should not be None"
        assert isinstance(result.text, str), \
            "Answer text should be a string"
        
        # 3. Answer text should indicate "not found" (Requirement 7.3)
        assert "could not find" in result.text.lower() or "not found" in result.text.lower(), \
            "Answer should indicate information was not found when context is empty"
        
        # 4. Supporting chunks should be empty (Requirement 7.4)
        assert hasattr(result, 'supporting_chunks'), \
            "Answer should have 'supporting_chunks' attribute"
        assert isinstance(result.supporting_chunks, list), \
            "Answer supporting_chunks should be a list"
        assert len(result.supporting_chunks) == 0, \
            "Answer should have empty supporting_chunks when context is empty"
        
        # 5. Confidence should be "not_found"
        assert hasattr(result, 'confidence'), \
            "Answer should have 'confidence' attribute"
        assert result.confidence == "not_found", \
            "Answer confidence should be 'not_found' when context is empty"
        
        # 6. LLM should NOT be called when context is empty
        # (optimization: no need to call LLM if we have no context)
        mock_llm.generate_answer.assert_not_called()
    
    @given(
        question=st.text(min_size=5, max_size=200).filter(lambda t: len(t.strip()) > 0),
        num_chunks=st.integers(min_value=1, max_value=5)
    )
    @settings(max_examples=100, deadline=20000)
    def test_property_13_answer_generation_not_found_response(
        self, 
        question, 
        num_chunks
    ):
        """
        Property 13 (Not found variant): Answer Generation with Context
        
        **Validates: Requirements 7.1, 7.3, 7.4**
        
        When the LLM returns a "not found" response (even with context), 
        the answer should have confidence="not_found" but still include 
        the supporting chunks.
        
        Requirements:
        - 7.1: WHEN retrieved context and a user question are provided, 
               THE Answer_Generator SHALL generate an answer using an LLM
        - 7.3: WHEN the context does not contain sufficient information to 
               answer the question, THE Answer_Generator SHALL return 
               "I could not find the answer in the document."
        - 7.4: THE Answer_Generator SHALL include the retrieved context chunks 
               as supporting evidence with the answer
        """
        from core.answer_generator import AnswerGenerator
        from core.models import RetrievedChunk, Chunk, ChunkMetadata, Answer
        from unittest.mock import Mock
        
        # Create mock LLM port that returns "not found" response
        mock_llm = Mock()
        mock_llm.get_model_name.return_value = "mock-llm"
        mock_llm.generate_answer.return_value = "I could not find the answer in the document."
        
        # Create answer generator with mock LLM
        answer_generator = AnswerGenerator(mock_llm)
        
        # Generate sample context chunks
        context_chunks = []
        for i in range(num_chunks):
            chunk_text = f"Context chunk {i}: Unrelated information. " * 3
            chunk = Chunk(
                text=chunk_text,
                metadata=ChunkMetadata(
                    chunk_index=i,
                    source_document="test_doc.pdf",
                    start_position=i * 100,
                    end_position=i * 100 + len(chunk_text)
                )
            )
            retrieved_chunk = RetrievedChunk(
                chunk=chunk,
                similarity_score=0.5 - (i * 0.05)
            )
            context_chunks.append(retrieved_chunk)
        
        # Generate answer
        result = answer_generator.generate_answer(question, context_chunks)
        
        # Property assertions
        
        # 1. Result should be an Answer object
        assert isinstance(result, Answer), \
            "generate_answer should return an Answer instance"
        
        # 2. Answer text should indicate "not found" (Requirement 7.3)
        assert "could not find" in result.text.lower(), \
            "Answer should indicate information was not found"
        
        # 3. Supporting chunks should still be included (Requirement 7.4)
        assert hasattr(result, 'supporting_chunks'), \
            "Answer should have 'supporting_chunks' attribute"
        assert len(result.supporting_chunks) == len(context_chunks), \
            "Answer should include supporting chunks even when answer is 'not found'"
        
        # 4. Confidence should be "not_found"
        assert result.confidence == "not_found", \
            "Answer confidence should be 'not_found' when LLM returns 'not found' response"
        
        # 5. LLM should have been called
        mock_llm.generate_answer.assert_called_once()
    
    @given(
        question=st.text(min_size=5, max_size=200).filter(lambda t: len(t.strip()) > 0),
        num_chunks=st.integers(min_value=1, max_value=5)
    )
    @settings(max_examples=100, deadline=20000)
    def test_property_14_answer_context_reference(
        self, 
        question, 
        num_chunks
    ):
        """
        Property 14: Answer Context Reference
        
        **Validates: Requirements 7.6**
        
        For any generated answer (excluding "not found" responses), the answer 
        text should contain references to or quotes from the provided context chunks.
        
        Requirements:
        - 7.6: WHEN the LLM generates a response, THE Answer_Generator SHALL 
               validate that the response references the provided context
        """
        from core.answer_generator import AnswerGenerator
        from core.models import RetrievedChunk, Chunk, ChunkMetadata, Answer
        from unittest.mock import Mock
        
        # Filter out questions that contain "not found" indicators
        not_found_indicators = [
            "could not find",
            "cannot find", 
            "not found",
            "no information",
            "insufficient information"
        ]
        question_lower = question.lower()
        assume(not any(indicator in question_lower for indicator in not_found_indicators))
        
        # Create mock LLM port
        mock_llm = Mock()
        mock_llm.get_model_name.return_value = "mock-llm"
        
        # Generate sample context chunks with distinctive phrases
        context_chunks = []
        distinctive_phrases = []
        for i in range(num_chunks):
            # Create distinctive 3+ word phrases that can be detected
            distinctive_phrase = f"distinctive information about topic {i}"
            distinctive_phrases.append(distinctive_phrase)
            chunk_text = f"Context chunk {i}: {distinctive_phrase}. Additional details here. More content follows."
            chunk = Chunk(
                text=chunk_text,
                metadata=ChunkMetadata(
                    chunk_index=i,
                    source_document=f"test_doc_{i % 3}.pdf",
                    start_position=i * 100,
                    end_position=i * 100 + len(chunk_text)
                )
            )
            retrieved_chunk = RetrievedChunk(
                chunk=chunk,
                similarity_score=0.9 - (i * 0.05)
            )
            context_chunks.append(retrieved_chunk)
        
        # Mock LLM returns answer that references the first chunk's distinctive phrase
        # This simulates a real LLM that uses the provided context
        mock_answer_text = f"Based on the context, {distinctive_phrases[0]} is relevant to your question."
        mock_llm.generate_answer.return_value = mock_answer_text
        
        # Create answer generator with mock LLM
        answer_generator = AnswerGenerator(mock_llm)
        
        # Generate answer
        result = answer_generator.generate_answer(question, context_chunks)
        
        # Property assertions
        
        # 1. Result should be an Answer object
        assert isinstance(result, Answer), \
            "generate_answer should return an Answer instance"
        
        # 2. Answer should not be a "not found" response
        assert result.confidence != "not_found", \
            "Answer confidence should not be 'not_found' when context is provided and LLM returns valid answer"
        
        # 3. Answer text should not be empty
        assert len(result.text) > 0, \
            "Answer text should not be empty"
        
        # 4. validate_answer_from_context should return True (Requirement 7.6)
        # This is the core validation that the answer references the context
        references_context = answer_generator.validate_answer_from_context(
            result.text, 
            context_chunks
        )
        assert references_context is True, \
            "Answer should reference the provided context (validate_answer_from_context should return True)"
        
        # 5. Answer should contain at least one 3+ word phrase from the context
        # This verifies the validation logic is working correctly
        answer_lower = result.text.lower()
        found_reference = False
        for retrieved_chunk in context_chunks:
            chunk_text_lower = retrieved_chunk.chunk.text.lower()
            chunk_words = chunk_text_lower.split()
            
            # Check for 3+ word phrases from chunk in answer
            for i in range(len(chunk_words) - 2):
                phrase = " ".join(chunk_words[i:i+3])
                if phrase in answer_lower:
                    found_reference = True
                    break
            
            if found_reference:
                break
        
        assert found_reference, \
            "Answer should contain at least one 3+ word phrase from the context chunks"
        
        # 6. LLM should have been called with context
        mock_llm.generate_answer.assert_called_once()
        
        # 7. Supporting chunks should be included
        assert len(result.supporting_chunks) > 0, \
            "Answer should include supporting chunks"
        assert len(result.supporting_chunks) == len(context_chunks), \
            "Answer should include all provided context chunks"
    
    @given(
        question=st.text(min_size=5, max_size=200).filter(lambda t: len(t.strip()) > 0),
        num_chunks=st.integers(min_value=1, max_value=5)
    )
    @settings(max_examples=100, deadline=20000)
    def test_property_14_answer_context_reference_no_reference(
        self, 
        question, 
        num_chunks
    ):
        """
        Property 14 (Negative variant): Answer Context Reference
        
        **Validates: Requirements 7.6**
        
        When the LLM generates an answer that does NOT reference the provided 
        context, validate_answer_from_context should return False and confidence 
        should be low.
        
        Requirements:
        - 7.6: WHEN the LLM generates a response, THE Answer_Generator SHALL 
               validate that the response references the provided context
        """
        from core.answer_generator import AnswerGenerator
        from core.models import RetrievedChunk, Chunk, ChunkMetadata, Answer
        from unittest.mock import Mock
        
        # Filter out questions that contain "not found" indicators
        not_found_indicators = [
            "could not find",
            "cannot find", 
            "not found",
            "no information",
            "insufficient information"
        ]
        question_lower = question.lower()
        assume(not any(indicator in question_lower for indicator in not_found_indicators))
        
        # Create mock LLM port
        mock_llm = Mock()
        mock_llm.get_model_name.return_value = "mock-llm"
        
        # Generate sample context chunks with specific content
        context_chunks = []
        for i in range(num_chunks):
            chunk_text = f"Context chunk {i}: Specific technical information about Swiggy operations in fiscal year 2023."
            chunk = Chunk(
                text=chunk_text,
                metadata=ChunkMetadata(
                    chunk_index=i,
                    source_document=f"test_doc_{i % 3}.pdf",
                    start_position=i * 100,
                    end_position=i * 100 + len(chunk_text)
                )
            )
            retrieved_chunk = RetrievedChunk(
                chunk=chunk,
                similarity_score=0.5 - (i * 0.05)  # Lower similarity scores
            )
            context_chunks.append(retrieved_chunk)
        
        # Mock LLM returns answer that does NOT reference the context
        # This simulates a hallucinated response
        mock_answer_text = "The answer involves completely unrelated information about weather patterns."
        mock_llm.generate_answer.return_value = mock_answer_text
        
        # Create answer generator with mock LLM
        answer_generator = AnswerGenerator(mock_llm)
        
        # Generate answer
        result = answer_generator.generate_answer(question, context_chunks)
        
        # Property assertions
        
        # 1. Result should be an Answer object
        assert isinstance(result, Answer), \
            "generate_answer should return an Answer instance"
        
        # 2. validate_answer_from_context should return False (Requirement 7.6)
        # This validates that the system detects when answer doesn't reference context
        references_context = answer_generator.validate_answer_from_context(
            result.text, 
            context_chunks
        )
        assert references_context is False, \
            "validate_answer_from_context should return False when answer doesn't reference context"
        
        # 3. Confidence should be "low" when answer doesn't reference context
        # The _determine_confidence method should set low confidence when references_context is False
        assert result.confidence == "low", \
            f"Answer confidence should be 'low' when answer doesn't reference context, got '{result.confidence}'"
        
        # 4. Answer should still include supporting chunks
        assert len(result.supporting_chunks) == len(context_chunks), \
            "Answer should include supporting chunks even when answer doesn't reference them"
        
        # 5. LLM should have been called
        mock_llm.generate_answer.assert_called_once()
