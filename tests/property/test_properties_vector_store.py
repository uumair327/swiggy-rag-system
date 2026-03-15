"""Property-based tests for Vector Store (FAISS Adapter) component.

**Validates: Requirements 4.1, 4.2, 4.3, 4.4**
"""

import os
import tempfile
import numpy as np
from hypothesis import given, strategies as st, settings

from adapters.faiss_adapter import FAISSAdapter
from core.models import Chunk, ChunkMetadata


class TestVectorStoreProperties:
    """Property-based tests for Vector Store (FAISS Adapter)."""

    @given(
        num_embeddings=st.integers(min_value=1, max_value=50),
        embedding_dim=st.sampled_from([128, 256, 384, 512]),
        top_k=st.integers(min_value=1, max_value=10),
    )
    @settings(max_examples=100, deadline=10000)
    def test_property_8_vector_store_retrieval_round_trip(
        self, num_embeddings, embedding_dim, top_k
    ):
        """
        Property 8: Vector Store Retrieval Round-Trip

        **Validates: Requirements 4.1, 4.2**

        For any embedding stored in the vector store with its associated chunk,
        searching with that same embedding should retrieve the original chunk
        in the results.

        Requirements:
        - 4.1: WHEN embeddings are provided, THE Vector_Store SHALL store the
               embeddings in a FAISS index
        - 4.2: WHEN storing embeddings, THE Vector_Store SHALL associate each
               embedding with its corresponding text chunk and metadata
        """
        # Initialize FAISS adapter with specified dimension
        vector_store = FAISSAdapter(dimension=embedding_dim)

        # Generate random embeddings (normalized to simulate real embeddings)
        embeddings_list = []
        chunks_list = []

        for i in range(num_embeddings):
            # Generate random embedding vector
            embedding = np.random.randn(embedding_dim).astype(np.float32)
            # Normalize to unit length (like sentence-transformers does)
            embedding = embedding / np.linalg.norm(embedding)
            embeddings_list.append(embedding)

            # Create corresponding chunk
            chunk = Chunk(
                text=f"This is test chunk number {i} with some content.",
                metadata=ChunkMetadata(
                    chunk_index=i,
                    source_document="test_document.pd",
                    start_position=i * 100,
                    end_position=(i + 1) * 100,
                ),
            )
            chunks_list.append(chunk)

        # Convert list to numpy array for batch storage
        embeddings_array = np.array(embeddings_list)

        # Store embeddings in vector store (Requirement 4.1)
        vector_store.add_embeddings(embeddings_array, chunks_list)

        # Property: Verify storage succeeded
        assert (
            vector_store.get_index_size() == num_embeddings
        ), f"Vector store should contain {num_embeddings} embeddings"

        # Round-trip test: Search with each stored embedding
        for i, (original_embedding, original_chunk) in enumerate(zip(embeddings_list, chunks_list)):
            # Search with the original embedding
            k = min(top_k, num_embeddings)
            results = vector_store.search(original_embedding, k)

            # Property assertions

            # 1. Search should return results
            assert len(results) > 0, f"Search with stored embedding {i} should return results"

            # 2. Results should be at most k items
            assert (
                len(results) <= k
            ), f"Search should return at most {k} results, got {len(results)}"

            # 3. Each result should be a tuple of (Chunk, float)
            for j, result in enumerate(results):
                assert isinstance(result, tuple), f"Result {j} should be a tuple"
                assert len(result) == 2, f"Result {j} should be a 2-tuple (Chunk, similarity_score)"

                chunk, similarity_score = result
                assert isinstance(chunk, Chunk), f"Result {j} first element should be a Chunk"
                assert isinstance(
                    similarity_score, float
                ), f"Result {j} second element should be a float"

            # 4. CRITICAL: The original chunk should be in the results (Requirement 4.2)
            # Since we're searching with the exact same embedding, it should be
            # the top result with distance ~0
            retrieved_chunks = [chunk for chunk, _ in results]
            retrieved_chunk_indices = [chunk.metadata.chunk_index for chunk in retrieved_chunks]

            assert original_chunk.metadata.chunk_index in retrieved_chunk_indices, (
                f"Original chunk {i} should be retrieved when searching with its embedding. "
                f"Retrieved indices: {retrieved_chunk_indices}"
            )

            # 5. The original chunk should be the top result (closest match)
            top_chunk, top_distance = results[0]
            assert top_chunk.metadata.chunk_index == original_chunk.metadata.chunk_index, (
                f"Original chunk {i} should be the top result. "
                f"Got chunk {top_chunk.metadata.chunk_index} instead"
            )

            # 6. Distance to itself should be very small (approximately 0)
            # For L2 distance of identical normalized vectors, distance should be ~0
            assert (
                top_distance < 1e-5
            ), f"Distance to identical embedding should be near 0, got {top_distance}"

            # 7. Retrieved chunk should have identical content to original
            assert (
                top_chunk.text == original_chunk.text
            ), "Retrieved chunk text should match original chunk text"

            # 8. Retrieved chunk metadata should match original
            assert (
                top_chunk.metadata.chunk_index == original_chunk.metadata.chunk_index
            ), "Retrieved chunk index should match original"
            assert (
                top_chunk.metadata.source_document == original_chunk.metadata.source_document
            ), "Retrieved chunk source_document should match original"
            assert (
                top_chunk.metadata.start_position == original_chunk.metadata.start_position
            ), "Retrieved chunk start_position should match original"
            assert (
                top_chunk.metadata.end_position == original_chunk.metadata.end_position
            ), "Retrieved chunk end_position should match original"

    @given(
        num_embeddings=st.integers(min_value=1, max_value=50),
        embedding_dim=st.sampled_from([128, 256, 384, 512]),
    )
    @settings(max_examples=100, deadline=10000)
    def test_property_9_vector_store_persistence_round_trip(self, num_embeddings, embedding_dim):
        """
        Property 9: Vector Store Persistence Round-Trip

        **Validates: Requirements 4.3, 4.4**

        For any vector store with stored embeddings, saving the index to disk
        and then loading it should preserve all embeddings and their associated chunks.

        Requirements:
        - 4.3: THE Vector_Store SHALL support saving the index to disk for persistence
        - 4.4: THE Vector_Store SHALL support loading a previously saved index from disk
        """
        # Initialize FAISS adapter with specified dimension
        vector_store_original = FAISSAdapter(dimension=embedding_dim)

        # Generate random embeddings and chunks
        embeddings_list = []
        chunks_list = []

        for i in range(num_embeddings):
            # Generate random embedding vector
            embedding = np.random.randn(embedding_dim).astype(np.float32)
            # Normalize to unit length (like sentence-transformers does)
            embedding = embedding / np.linalg.norm(embedding)
            embeddings_list.append(embedding)

            # Create corresponding chunk with unique content
            chunk = Chunk(
                text=f"Unique test chunk {i} with specific content for persistence testing.",
                metadata=ChunkMetadata(
                    chunk_index=i,
                    source_document=f"test_document_{i % 3}.pd",
                    start_position=i * 150,
                    end_position=(i + 1) * 150,
                ),
            )
            chunks_list.append(chunk)

        # Convert list to numpy array for batch storage
        embeddings_array = np.array(embeddings_list)

        # Store embeddings in original vector store
        vector_store_original.add_embeddings(embeddings_array, chunks_list)

        # Verify original storage
        assert (
            vector_store_original.get_index_size() == num_embeddings
        ), f"Original vector store should contain {num_embeddings} embeddings"

        # Create temporary file for persistence testing
        with tempfile.TemporaryDirectory() as temp_dir:
            index_path = os.path.join(temp_dir, "test_index")

            # Save index to disk (Requirement 4.3)
            vector_store_original.save_index(index_path)

            # Verify files were created
            assert os.path.exists(f"{index_path}.faiss"), "FAISS index file should be created"
            assert os.path.exists(
                f"{index_path}.chunks.pkl"
            ), "Chunks metadata file should be created"

            # Create new vector store instance and load from disk (Requirement 4.4)
            vector_store_loaded = FAISSAdapter(dimension=embedding_dim)
            vector_store_loaded.load_index(index_path)

            # Property assertions: Verify persistence preserved everything

            # 1. Index size should be preserved
            assert vector_store_loaded.get_index_size() == num_embeddings, (
                f"Loaded vector store should contain {num_embeddings} embeddings, "
                f"got {vector_store_loaded.get_index_size()}"
            )

            # 2. Chunks list should be preserved
            assert len(vector_store_loaded.chunks) == num_embeddings, (
                f"Loaded vector store should have {num_embeddings} chunks, "
                f"got {len(vector_store_loaded.chunks)}"
            )

            # 3. Each chunk should be preserved with identical content and metadata
            for i, (original_chunk, loaded_chunk) in enumerate(
                zip(chunks_list, vector_store_loaded.chunks)
            ):
                assert (
                    loaded_chunk.text == original_chunk.text
                ), f"Chunk {i} text should be preserved after save/load"
                assert (
                    loaded_chunk.metadata.chunk_index == original_chunk.metadata.chunk_index
                ), f"Chunk {i} index should be preserved"
                assert (
                    loaded_chunk.metadata.source_document == original_chunk.metadata.source_document
                ), f"Chunk {i} source_document should be preserved"
                assert (
                    loaded_chunk.metadata.start_position == original_chunk.metadata.start_position
                ), f"Chunk {i} start_position should be preserved"
                assert (
                    loaded_chunk.metadata.end_position == original_chunk.metadata.end_position
                ), f"Chunk {i} end_position should be preserved"

            # 4. CRITICAL: Embeddings should be preserved (test via search)
            # Search with each original embedding in the loaded index
            for i, original_embedding in enumerate(embeddings_list):
                results = vector_store_loaded.search(original_embedding, top_k=1)

                # Should find at least one result
                assert (
                    len(results) > 0
                ), f"Search with embedding {i} should return results after load"

                # Top result should be the original chunk (distance ~0)
                top_chunk, top_distance = results[0]
                assert top_chunk.metadata.chunk_index == i, (
                    f"Loaded index should retrieve original chunk {i}, "
                    f"got chunk {top_chunk.metadata.chunk_index}"
                )

                # Distance should be very small (embeddings preserved accurately)
                assert top_distance < 1e-5, (
                    "Distance to original embedding should be near 0 after persistence, "
                    f"got {top_distance} for chunk {i}"
                )

            # 5. Verify search results are identical between original and loaded
            # Pick a random embedding to test comprehensive search behavior
            test_idx = num_embeddings // 2
            test_embedding = embeddings_list[test_idx]
            k = min(5, num_embeddings)

            original_results = vector_store_original.search(test_embedding, k)
            loaded_results = vector_store_loaded.search(test_embedding, k)

            assert len(original_results) == len(
                loaded_results
            ), "Original and loaded vector stores should return same number of results"

            for j, (orig_result, loaded_result) in enumerate(zip(original_results, loaded_results)):
                orig_chunk, orig_distance = orig_result
                loaded_chunk, loaded_distance = loaded_result

                assert (
                    orig_chunk.metadata.chunk_index == loaded_chunk.metadata.chunk_index
                ), f"Result {j}: chunk indices should match"
                assert abs(orig_distance - loaded_distance) < 1e-5, (
                    f"Result {j}: distances should match (orig: {orig_distance}, "
                    f"loaded: {loaded_distance})"
                )

    @given(
        num_embeddings=st.integers(min_value=1, max_value=100),
        embedding_dim=st.sampled_from([128, 256, 384, 512]),
        k=st.integers(min_value=1, max_value=20),
    )
    @settings(max_examples=100, deadline=10000)
    def test_property_10_top_k_retrieval_correctness(self, num_embeddings, embedding_dim, k):
        """
        Property 10: Top-K Retrieval Correctness

        **Validates: Requirements 4.5, 6.2, 6.4**

        For any query embedding and value K, the vector store should return
        at most K chunks, ranked in descending order by similarity score.

        Requirements:
        - 4.5: WHEN a query embedding is provided, THE Vector_Store SHALL retrieve
               the top K most similar embeddings within 500 milliseconds
        - 6.2: THE Context_Retriever SHALL retrieve the top 5 most similar chunks
               from the Vector_Store
        - 6.4: THE Context_Retriever SHALL rank retrieved chunks by similarity
               score in descending order
        """
        # Initialize FAISS adapter with specified dimension
        vector_store = FAISSAdapter(dimension=embedding_dim)

        # Generate random embeddings and chunks
        embeddings_list = []
        chunks_list = []

        for i in range(num_embeddings):
            # Generate random embedding vector
            embedding = np.random.randn(embedding_dim).astype(np.float32)
            # Normalize to unit length (like sentence-transformers does)
            embedding = embedding / np.linalg.norm(embedding)
            embeddings_list.append(embedding)

            # Create corresponding chunk
            chunk = Chunk(
                text=f"Test chunk {i} with content for top-k retrieval testing.",
                metadata=ChunkMetadata(
                    chunk_index=i,
                    source_document="test_document.pd",
                    start_position=i * 100,
                    end_position=(i + 1) * 100,
                ),
            )
            chunks_list.append(chunk)

        # Convert list to numpy array for batch storage
        embeddings_array = np.array(embeddings_list)

        # Store embeddings in vector store
        vector_store.add_embeddings(embeddings_array, chunks_list)

        # Generate a random query embedding (different from stored embeddings)
        query_embedding = np.random.randn(embedding_dim).astype(np.float32)
        query_embedding = query_embedding / np.linalg.norm(query_embedding)

        # Perform search with top_k = k
        results = vector_store.search(query_embedding, top_k=k)

        # Property assertions

        # 1. CRITICAL: Results should contain at most K items (Requirement 4.5, 6.2)
        expected_count = min(k, num_embeddings)
        assert len(results) <= k, f"Search should return at most {k} results, got {len(results)}"

        assert len(results) == expected_count, (
            f"Search should return exactly {expected_count} results "
            f"(min of k={k} and num_embeddings={num_embeddings}), got {len(results)}"
        )

        # 2. Each result should be a tuple of (Chunk, float)
        for i, result in enumerate(results):
            assert isinstance(result, tuple), f"Result {i} should be a tuple"
            assert len(result) == 2, f"Result {i} should be a 2-tuple (Chunk, similarity_score)"

            chunk, similarity_score = result
            assert isinstance(chunk, Chunk), f"Result {i} first element should be a Chunk"
            assert isinstance(
                similarity_score, float
            ), f"Result {i} second element should be a float"
            assert (
                similarity_score >= 0
            ), f"Result {i} similarity score should be non-negative, got {similarity_score}"

        # 3. CRITICAL: Results should be ranked by similarity in ASCENDING order
        # (Requirement 6.4 - descending similarity = ascending distance)
        # FAISS returns L2 distances where lower distance = higher similarity
        # So results should be in ascending order of distance values
        if len(results) > 1:
            distances = [distance for _, distance in results]

            for i in range(len(distances) - 1):
                assert distances[i] <= distances[i + 1], (
                    "Results should be ranked by ascending distance (descending similarity). "
                    f"Distance at position {i} ({distances[i]:.4f}) should be <= "
                    f"distance at position {i+1} ({distances[i+1]:.4f})"
                )

        # 4. All returned chunks should be unique (no duplicates)
        chunk_indices = [chunk.metadata.chunk_index for chunk, _ in results]
        assert len(chunk_indices) == len(set(chunk_indices)), (
            "Results should not contain duplicate chunks. " f"Found indices: {chunk_indices}"
        )

        # 5. All returned chunks should be from the stored chunks
        stored_indices = {chunk.metadata.chunk_index for chunk in chunks_list}
        for chunk, _ in results:
            assert (
                chunk.metadata.chunk_index in stored_indices
            ), f"Retrieved chunk {chunk.metadata.chunk_index} should be from stored chunks"

        # 6. Test edge case: k > num_embeddings should return all embeddings
        large_k = num_embeddings + 50
        all_results = vector_store.search(query_embedding, top_k=large_k)
        assert len(all_results) == num_embeddings, (
            f"Search with k={large_k} > num_embeddings={num_embeddings} "
            f"should return all {num_embeddings} embeddings, got {len(all_results)}"
        )
