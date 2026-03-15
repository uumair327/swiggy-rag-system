"""Context Retriever component for retrieving relevant document chunks."""

import logging
from typing import List
from core.models import Embedding, RetrievedChunk
from ports.outbound import VectorStorePort

logger = logging.getLogger(__name__)


class ContextRetriever:
    """
    Retrieves relevant document chunks for a query using vector similarity search.

    This component uses a VectorStorePort to search for chunks that are semantically
    similar to the query embedding, filters results by similarity threshold, and
    returns them sorted by relevance.
    """

    def __init__(
        self, vector_store_port: VectorStorePort, top_k: int = 5, similarity_threshold: float = 0.3
    ):
        """
        Initialize the ContextRetriever with a vector store.

        Args:
            vector_store_port: Implementation of VectorStorePort for similarity search
            top_k: Default number of chunks to retrieve
            similarity_threshold: Default minimum similarity score for inclusion
        """
        self.vector_store = vector_store_port
        self.default_top_k = top_k
        self.default_similarity_threshold = similarity_threshold
        logger.info(
            f"ContextRetriever initialized with top_k={top_k}, "
            f"similarity_threshold={similarity_threshold}"
        )

    def retrieve_context(
        self, query_embedding: Embedding, top_k: int = None, similarity_threshold: float = None
    ) -> List[RetrievedChunk]:
        """
        Retrieve relevant document chunks for a query embedding.

        This method searches the vector store for chunks similar to the query,
        filters out results below the similarity threshold, and returns them
        sorted by similarity score in descending order.

        Args:
            query_embedding: The embedding representation of the user's query
            top_k: Maximum number of chunks to retrieve (uses default if None)
            similarity_threshold: Minimum similarity score for inclusion (uses default if None)

        Returns:
            List of RetrievedChunk objects sorted by similarity score (highest first).
            Returns empty list if no chunks meet the threshold.
        """
        # Use defaults if not provided
        if top_k is None:
            top_k = self.default_top_k
        if similarity_threshold is None:
            similarity_threshold = self.default_similarity_threshold

        logger.info(f"Retrieving context: top_k={top_k}, threshold={similarity_threshold}")

        # Search the vector store for similar chunks
        search_results = self.vector_store.search(
            query_embedding=query_embedding.vector, top_k=top_k
        )

        logger.debug(f"Vector store returned {len(search_results)} results")

        # Filter results by similarity threshold and convert to RetrievedChunk objects
        retrieved_chunks = []
        for chunk, similarity_score in search_results:
            if similarity_score >= similarity_threshold:
                retrieved_chunks.append(
                    RetrievedChunk(chunk=chunk, similarity_score=similarity_score)
                )
                logger.debug(
                    f"Retrieved chunk {chunk.metadata.chunk_index} from "
                    f"{chunk.metadata.source_document} with score {similarity_score:.4f}"
                )
            else:
                logger.debug(
                    f"Filtered out chunk {chunk.metadata.chunk_index} "
                    f"with score {similarity_score:.4f} (below threshold)"
                )

        # Sort by similarity score in descending order
        # (should already be sorted from vector store, but ensure it)
        retrieved_chunks.sort(key=lambda rc: rc.similarity_score, reverse=True)

        logger.info(f"Context retrieval complete: {len(retrieved_chunks)} chunks above threshold")

        return retrieved_chunks
