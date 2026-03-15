"""Property-based tests for Embedding Generator component.

**Validates: Requirements 3.1**
"""

import pytest
import numpy as np
from hypothesis import given, strategies as st, assume, settings

from core.embedding_generator import EmbeddingGenerator
from core.models import Embedding


class TestEmbeddingGeneratorProperties:
    """Property-based tests for EmbeddingGenerator."""
    
    @given(
        text=st.text(min_size=1, max_size=1000)
    )
    @settings(max_examples=100, deadline=10000)
    def test_property_5_embedding_generation_success(self, embedding_model_cached, text):
        """
        Property 5: Embedding Generation Success
        
        **Validates: Requirements 3.1**
        
        For any text input, the EmbeddingGenerator should produce a numerical 
        vector with non-zero values.
        
        Requirements:
        - 3.1: WHEN a text chunk is provided, THE Embedding_Generator SHALL 
               generate a vector embedding using the sentence-transformers model
        """
        # Skip empty or whitespace-only text
        assume(len(text.strip()) > 0)
        
        # Use the session-cached embedding model from conftest
        generator = EmbeddingGenerator(embedding_model_cached)
        embedding_model = embedding_model_cached
        
        # Generate embedding (Requirement 3.1)
        result = generator.generate_embedding(text)
        
        # Property assertions
        
        # 1. Result should be an Embedding object
        assert isinstance(result, Embedding), \
            "generate_embedding should return Embedding instance"
        
        # 2. Embedding should have a vector attribute
        assert hasattr(result, 'vector'), \
            "Embedding should have vector attribute"
        assert result.vector is not None, \
            "Embedding vector should not be None"
        
        # 3. Vector should be a numpy array (numerical vector)
        assert isinstance(result.vector, np.ndarray), \
            "Embedding vector should be a numpy array"
        
        # 4. Vector should have non-zero values (Requirement 3.1)
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
        expected_dim = embedding_model.get_embedding_dimension()
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
        assert result.source_text == text, \
            "Embedding source_text should match input text"
        
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
        texts=st.lists(
            st.text(min_size=1, max_size=500).filter(lambda t: len(t.strip()) > 0),
            min_size=1,
            max_size=20
        )
    )
    @settings(max_examples=100, deadline=15000)
    def test_property_6_batch_embedding_completeness(self, embedding_model_cached, texts):
        """
        Property 6: Batch Embedding Completeness
        
        **Validates: Requirements 3.3**
        
        For any list of text chunks, batch embedding generation should produce 
        exactly one embedding per chunk.
        
        Requirements:
        - 3.3: WHEN multiple chunks are provided, THE Embedding_Generator SHALL 
               generate embeddings for all chunks in batch
        """
        # Use the session-cached embedding model from conftest
        generator = EmbeddingGenerator(embedding_model_cached)
        embedding_model = embedding_model_cached
        
        # Generate batch embeddings (Requirement 3.3)
        results = generator.generate_embeddings_batch(texts)
        
        # Property assertions
        
        # 1. Result should be a list
        assert isinstance(results, list), \
            "generate_embeddings_batch should return a list"
        
        # 2. Should produce exactly one embedding per input text (Requirement 3.3)
        assert len(results) == len(texts), \
            f"Should produce one embedding per input: expected {len(texts)}, got {len(results)}"
        
        # 3. All results should be Embedding objects
        for i, result in enumerate(results):
            assert isinstance(result, Embedding), \
                f"Result at index {i} should be an Embedding instance"
        
        # 4. All embeddings should have vectors
        for i, result in enumerate(results):
            assert hasattr(result, 'vector'), \
                f"Embedding at index {i} should have vector attribute"
            assert result.vector is not None, \
                f"Embedding vector at index {i} should not be None"
            assert isinstance(result.vector, np.ndarray), \
                f"Embedding vector at index {i} should be a numpy array"
        
        # 5. All embeddings should have the same dimensionality
        expected_dim = embedding_model.get_embedding_dimension()
        for i, result in enumerate(results):
            assert len(result.vector) == expected_dim, \
                f"Embedding at index {i} should have dimension {expected_dim}, got {len(result.vector)}"
        
        # 6. All embeddings should have non-zero values
        for i, result in enumerate(results):
            assert np.any(result.vector != 0), \
                f"Embedding at index {i} should contain non-zero values"
        
        # 7. All embeddings should have valid numerical values (not NaN or Inf)
        for i, result in enumerate(results):
            assert not np.any(np.isnan(result.vector)), \
                f"Embedding at index {i} should not contain NaN values"
            assert not np.any(np.isinf(result.vector)), \
                f"Embedding at index {i} should not contain infinite values"
        
        # 8. All embeddings should be normalized
        for i, result in enumerate(results):
            norm = np.linalg.norm(result.vector)
            assert np.isclose(norm, 1.0, atol=1e-5), \
                f"Embedding at index {i} should be normalized (L2 norm ≈ 1.0), got {norm}"
        
        # 9. Source text should be preserved for all embeddings
        for i, result in enumerate(results):
            assert hasattr(result, 'source_text'), \
                f"Embedding at index {i} should have source_text attribute"
            assert result.source_text == texts[i], \
                f"Embedding at index {i} source_text should match input text"
        
        # 10. Different texts should produce different embeddings
        # (with high probability for random texts)
        if len(results) > 1:
            # Check that not all embeddings are identical
            first_vector = results[0].vector
            all_identical = all(
                np.allclose(result.vector, first_vector, atol=1e-6)
                for result in results[1:]
            )
            # For random texts, embeddings should differ
            # (This may occasionally fail for very similar generated texts, but unlikely)
            if len(set(texts)) > 1:  # Only check if input texts are different
                assert not all_identical, \
                    "Different input texts should produce different embeddings"
    
    @given(
        texts=st.lists(
            st.text(min_size=1, max_size=500).filter(lambda t: len(t.strip()) > 0),
            min_size=2,
            max_size=20
        )
    )
    @settings(max_examples=100, deadline=15000)
    def test_property_7_embedding_dimensionality_consistency(self, embedding_model_cached, texts):
        """
        Property 7: Embedding Dimensionality Consistency
        
        **Validates: Requirements 3.4, 5.3**
        
        For any set of embeddings generated by the system (whether from chunks 
        or queries), all embeddings should have the same dimensionality.
        
        Requirements:
        - 3.4: THE Embedding_Generator SHALL return embeddings as numerical 
               vectors with consistent dimensionality
        - 5.3: WHEN a valid question is received, THE Query_Handler SHALL 
               generate an embedding for the question using the same model 
               as document chunks
        """
        # Use the session-cached embedding model from conftest
        generator = EmbeddingGenerator(embedding_model_cached)
        embedding_model = embedding_model_cached
        
        # Generate embeddings for all texts (simulating both chunks and queries)
        embeddings = []
        
        # Generate single embeddings (simulating query processing)
        for text in texts[:len(texts)//2] if len(texts) > 1 else texts:
            embedding = generator.generate_embedding(text)
            embeddings.append(embedding)
        
        # Generate batch embeddings (simulating chunk processing)
        if len(texts) > len(texts)//2:
            batch_embeddings = generator.generate_embeddings_batch(texts[len(texts)//2:])
            embeddings.extend(batch_embeddings)
        
        # Property assertions
        
        # 1. Should have generated embeddings
        assert len(embeddings) > 0, \
            "Should have generated at least one embedding"
        
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
        
        # 4. CRITICAL: All embeddings should have the SAME dimensionality (Requirement 3.4)
        expected_dim = embedding_model.get_embedding_dimension()
        dimensions = [len(embedding.vector) for embedding in embeddings]
        
        assert all(dim == expected_dim for dim in dimensions), \
            f"All embeddings should have dimension {expected_dim}, got dimensions: {set(dimensions)}"
        
        # 5. Verify consistency across single and batch generation methods
        # Both methods should produce embeddings with the same dimensionality
        if len(embeddings) > 1:
            first_dim = len(embeddings[0].vector)
            for i, embedding in enumerate(embeddings[1:], start=1):
                assert len(embedding.vector) == first_dim, \
                    f"Embedding at index {i} has dimension {len(embedding.vector)}, " \
                    f"expected {first_dim} (same as first embedding)"
        
        # 6. Verify all embeddings are valid numerical vectors
        for i, embedding in enumerate(embeddings):
            assert not np.any(np.isnan(embedding.vector)), \
                f"Embedding at index {i} should not contain NaN values"
            assert not np.any(np.isinf(embedding.vector)), \
                f"Embedding at index {i} should not contain infinite values"
        
        # 7. Verify all embeddings are normalized (consistent with model behavior)
        for i, embedding in enumerate(embeddings):
            norm = np.linalg.norm(embedding.vector)
            assert np.isclose(norm, 1.0, atol=1e-5), \
                f"Embedding at index {i} should be normalized (L2 norm ≈ 1.0), got {norm}"
