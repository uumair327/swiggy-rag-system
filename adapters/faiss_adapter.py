"""FAISS adapter implementing VectorStorePort for vector storage and similarity search."""

import os
import pickle
import logging
from typing import List, Tuple
import numpy as np
import faiss

from ports.outbound import VectorStorePort
from core.models import Chunk

logger = logging.getLogger(__name__)


class FAISSAdapter(VectorStorePort):
    """
    FAISS-based implementation of VectorStorePort.

    Uses FAISS IndexFlatL2 for L2 distance-based similarity search.
    Maintains separate storage for chunk metadata.
    """

    def __init__(self, dimension: int):
        """
        Initialize FAISS adapter with specified embedding dimension.

        Args:
            dimension: Dimensionality of the embeddings to be stored
        """
        logger.info(f"FAISSAdapter: Initializing with dimension {dimension}")
        self.dimension = dimension
        self.index = faiss.IndexFlatL2(dimension)
        self.chunks: List[Chunk] = []
        logger.info("FAISSAdapter: Initialized successfully")

    def add_embeddings(self, embeddings: np.ndarray, chunks: List[Chunk]) -> None:
        """
        Store embeddings with associated chunks.

        Args:
            embeddings: Numpy array of shape (n, embedding_dim)
            chunks: List of Chunk objects corresponding to embeddings

        Raises:
            ValueError: If embeddings and chunks have mismatched lengths
            ValueError: If embedding dimension doesn't match index dimension
        """
        logger.info(f"FAISSAdapter: Adding {len(embeddings)} embeddings to index")

        if len(embeddings) != len(chunks):
            error_msg = (
                f"Embeddings count ({len(embeddings)}) must match chunks count ({len(chunks)})"
            )
            logger.error(f"FAISSAdapter: {error_msg}")
            raise ValueError(error_msg)

        if embeddings.shape[1] != self.dimension:
            error_msg = (
                f"Embedding dimension ({embeddings.shape[1]}) must match "
                f"index dimension ({self.dimension})"
            )
            logger.error(f"FAISSAdapter: {error_msg}")
            raise ValueError(error_msg)

        # Ensure embeddings are float32 for FAISS
        embeddings_float32 = embeddings.astype(np.float32)

        # Add embeddings to FAISS index
        self.index.add(embeddings_float32)

        # Store corresponding chunks
        self.chunks.extend(chunks)

        logger.info(
            f"FAISSAdapter: Successfully added embeddings, "
            f"total index size: {self.get_index_size()}"
        )

    def search(self, query_embedding: np.ndarray, top_k: int) -> List[Tuple[Chunk, float]]:
        """
        Search for similar embeddings.

        Args:
            query_embedding: Query vector of shape (embedding_dim,) or (1, embedding_dim)
            top_k: Number of results to return

        Returns:
            List of tuples (Chunk, similarity_score) sorted by similarity (lower distance = higher similarity)
        """
        if self.get_index_size() == 0:
            logger.warning("FAISSAdapter: Search called on empty index")
            return []

        logger.debug(f"FAISSAdapter: Searching for top {top_k} similar chunks")

        # Reshape query embedding if needed
        if query_embedding.ndim == 1:
            query_embedding = query_embedding.reshape(1, -1)

        # Ensure query is float32
        query_float32 = query_embedding.astype(np.float32)

        # Limit top_k to available chunks
        k = min(top_k, self.get_index_size())

        # Search FAISS index (returns distances and indices)
        distances, indices = self.index.search(query_float32, k)

        # Build results list with chunks and similarity scores
        results = []
        for distance, idx in zip(distances[0], indices[0]):
            if idx != -1:  # FAISS returns -1 for empty slots
                chunk = self.chunks[idx]
                # Convert L2 distance to similarity score (lower distance = higher similarity)
                # We return the distance as-is; the caller can interpret it
                results.append((chunk, float(distance)))
                logger.debug(
                    f"FAISSAdapter: Found chunk {chunk.metadata.chunk_index} "
                    f"with distance {distance:.4f}"
                )

        logger.debug(f"FAISSAdapter: Search returned {len(results)} results")
        return results

    def save_index(self, file_path: str) -> None:
        """
        Persist index to disk.

        Saves both the FAISS index and the chunk metadata.

        Args:
            file_path: Path where the index should be saved (without extension)
        """
        logger.info(f"FAISSAdapter: Saving index to {file_path}")

        # Create directory if it doesn't exist
        os.makedirs(
            os.path.dirname(file_path) if os.path.dirname(file_path) else ".", exist_ok=True
        )

        # Save FAISS index
        faiss.write_index(self.index, f"{file_path}.faiss")
        logger.debug(f"FAISSAdapter: FAISS index saved to {file_path}.faiss")

        # Save chunks metadata separately
        with open(f"{file_path}.chunks.pkl", "wb") as f:
            pickle.dump(self.chunks, f)
        logger.debug(f"FAISSAdapter: Chunks metadata saved to {file_path}.chunks.pkl")

        logger.info(
            f"FAISSAdapter: Index saved successfully with {self.get_index_size()} embeddings"
        )

    def load_index(self, file_path: str) -> None:
        """
        Load index from disk.

        Loads both the FAISS index and the chunk metadata.

        Args:
            file_path: Path to the saved index (without extension)

        Raises:
            FileNotFoundError: If the index file does not exist
        """
        logger.info(f"FAISSAdapter: Loading index from {file_path}")

        faiss_path = f"{file_path}.faiss"
        chunks_path = f"{file_path}.chunks.pkl"

        if not os.path.exists(faiss_path):
            logger.error(f"FAISSAdapter: FAISS index file not found: {faiss_path}")
            raise FileNotFoundError(f"FAISS index file not found: {faiss_path}")

        if not os.path.exists(chunks_path):
            logger.error(f"FAISSAdapter: Chunks metadata file not found: {chunks_path}")
            raise FileNotFoundError(f"Chunks metadata file not found: {chunks_path}")

        # Load FAISS index
        self.index = faiss.read_index(faiss_path)
        logger.debug(f"FAISSAdapter: FAISS index loaded from {faiss_path}")

        # Load chunks metadata
        with open(chunks_path, "rb") as f:
            self.chunks = pickle.load(f)
        logger.debug(f"FAISSAdapter: Chunks metadata loaded from {chunks_path}")

        logger.info(
            f"FAISSAdapter: Index loaded successfully with {self.get_index_size()} embeddings"
        )

    def get_index_size(self) -> int:
        """
        Return number of stored embeddings.

        Returns:
            Integer count of embeddings in the index
        """
        return self.index.ntotal
