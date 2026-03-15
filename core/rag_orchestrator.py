"""RAG Orchestrator component that coordinates the complete RAG workflow."""

import logging
import os
import time
from typing import Optional

from core.document_processor import DocumentProcessor
from core.text_chunker import TextChunker
from core.embedding_generator import EmbeddingGenerator
from core.query_handler import QueryHandler
from core.context_retriever import ContextRetriever
from core.answer_generator import AnswerGenerator
from core.models import IngestionResult, QueryResult, Answer
from ports.outbound import VectorStorePort


logger = logging.getLogger(__name__)


class RAGOrchestrator:
    """
    Orchestrates the complete RAG workflow from document ingestion to answer generation.
    
    This component coordinates all core domain components to provide two main workflows:
    1. Document Ingestion: load → chunk → embed → store → persist
    2. Query Processing: validate → embed → retrieve → generate → return
    
    The orchestrator follows Hexagonal Architecture principles by depending on
    core domain components and port interfaces rather than concrete implementations.
    """
    
    def __init__(
        self,
        document_processor: DocumentProcessor,
        text_chunker: TextChunker,
        embedding_generator: EmbeddingGenerator,
        query_handler: QueryHandler,
        context_retriever: ContextRetriever,
        answer_generator: AnswerGenerator,
        vector_store: VectorStorePort,
        index_path: Optional[str] = None
    ):
        """
        Initialize RAGOrchestrator with all required components.
        
        Args:
            document_processor: Component for loading and processing documents
            text_chunker: Component for splitting text into chunks
            embedding_generator: Component for generating embeddings
            query_handler: Component for processing user questions
            context_retriever: Component for retrieving relevant chunks
            answer_generator: Component for generating answers
            vector_store: Port for vector storage and similarity search
            index_path: Optional path for persisting the vector index
        """
        self.document_processor = document_processor
        self.text_chunker = text_chunker
        self.embedding_generator = embedding_generator
        self.query_handler = query_handler
        self.context_retriever = context_retriever
        self.answer_generator = answer_generator
        self.vector_store = vector_store
        self.index_path = index_path
        
        logger.info("RAGOrchestrator initialized with all components")
        
        # Auto-load existing index if available
        if index_path and os.path.exists(index_path + ".faiss"):
            try:
                logger.info(f"Found existing index at {index_path}, loading...")
                self.vector_store.load_index(index_path)
                logger.info(f"Index loaded successfully with {self.vector_store.get_index_size()} embeddings")
            except Exception as e:
                logger.warning(f"Could not load existing index: {e}")
    
    def ingest_document(self, file_path: str) -> IngestionResult:
        """
        Ingest a document through the complete workflow.
        
        Workflow: load → chunk → embed → store → persist
        
        Args:
            file_path: Path to the PDF document to ingest
            
        Returns:
            IngestionResult with success status, counts, and any error messages
        """
        logger.info(f"Starting document ingestion for: {file_path}")
        
        try:
            # Step 1: Load document
            logger.info("Step 1/5: Loading document...")
            document_content = self.document_processor.load_document(file_path)
            logger.info(
                f"Document loaded successfully: {document_content.page_count} pages, "
                f"{len(document_content.text)} characters"
            )
            
            # Step 2: Chunk text
            logger.info("Step 2/5: Chunking text...")
            chunks = self.text_chunker.chunk_text(
                text=document_content.text,
                source_name=document_content.source_path
            )
            logger.info(f"Created {len(chunks)} chunks")
            
            # Validate chunk coverage
            coverage_result = self.text_chunker.validate_chunk_coverage(
                original_text=document_content.text,
                chunks=chunks
            )
            if not coverage_result.is_complete:
                logger.warning(
                    f"Chunk coverage validation found {len(coverage_result.missing_segments)} "
                    f"missing segments"
                )
            
            # Step 3: Generate embeddings
            logger.info("Step 3/5: Generating embeddings...")
            chunk_texts = [chunk.text for chunk in chunks]
            embeddings = self.embedding_generator.generate_embeddings_batch(chunk_texts)
            logger.info(f"Generated {len(embeddings)} embeddings")
            
            # Step 4: Store in vector database
            logger.info("Step 4/5: Storing embeddings in vector store...")
            import numpy as np
            embedding_vectors = np.array([emb.vector for emb in embeddings])
            self.vector_store.add_embeddings(
                embeddings=embedding_vectors,
                chunks=chunks
            )
            stored_count = self.vector_store.get_index_size()
            logger.info(f"Stored {stored_count} embeddings in vector store")
            
            # Step 5: Persist index to disk (if path provided)
            if self.index_path:
                logger.info(f"Step 5/5: Persisting index to {self.index_path}...")
                self.vector_store.save_index(self.index_path)
                logger.info("Index saved successfully")
            else:
                logger.info("Step 5/5: Skipping persistence (no index path provided)")
            
            logger.info("Document ingestion completed successfully")
            return IngestionResult(
                success=True,
                chunks_created=len(chunks),
                embeddings_stored=stored_count,
                error_message=None
            )
            
        except FileNotFoundError as e:
            error_msg = str(e)
            logger.error(f"Document ingestion failed - file not found: {error_msg}")
            return IngestionResult(
                success=False,
                chunks_created=0,
                embeddings_stored=0,
                error_message=error_msg
            )
        
        except ValueError as e:
            error_msg = str(e)
            logger.error(f"Document ingestion failed - validation error: {error_msg}")
            return IngestionResult(
                success=False,
                chunks_created=0,
                embeddings_stored=0,
                error_message=error_msg
            )
        
        except Exception as e:
            error_msg = f"Unexpected error during document ingestion: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return IngestionResult(
                success=False,
                chunks_created=0,
                embeddings_stored=0,
                error_message=error_msg
            )
    
    def process_query(self, question: str) -> QueryResult:
        """
        Process a user query through the complete workflow.
        
        Workflow: validate → embed → retrieve → generate → return
        
        Args:
            question: User's natural language question
            
        Returns:
            QueryResult with answer and processing time
        """
        start_time = time.time()
        logger.info(f"Starting query processing: {question[:100]}...")
        
        try:
            # Check if system is ready
            if not self.validate_system_ready():
                error_msg = (
                    "Error: Vector store not initialized. "
                    "Please ingest a document first."
                )
                logger.error(error_msg)
                answer = Answer(
                    text=error_msg,
                    supporting_chunks=[],
                    confidence="not_found"
                )
                processing_time = time.time() - start_time
                return QueryResult(
                    answer=answer,
                    processing_time_seconds=processing_time
                )
            
            # Step 1: Validate and embed question
            logger.info("Step 1/4: Validating and embedding question...")
            query_embedding = self.query_handler.process_question(question)
            logger.info(
                f"Query embedding generated (dimension: {query_embedding.dimension})"
            )
            
            # Step 2: Retrieve relevant context
            logger.info("Step 2/4: Retrieving relevant context...")
            retrieved_chunks = self.context_retriever.retrieve_context(
                query_embedding=query_embedding,
                top_k=5,
                similarity_threshold=0.3
            )
            logger.info(
                f"Retrieved {len(retrieved_chunks)} chunks above similarity threshold"
            )
            
            if retrieved_chunks:
                avg_similarity = sum(
                    chunk.similarity_score for chunk in retrieved_chunks
                ) / len(retrieved_chunks)
                logger.info(f"Average similarity score: {avg_similarity:.3f}")
            
            # Step 3: Generate answer
            logger.info("Step 3/4: Generating answer...")
            answer = self.answer_generator.generate_answer(
                question=question,
                context=retrieved_chunks
            )
            logger.info(
                f"Answer generated with confidence: {answer.confidence}"
            )
            
            # Step 4: Return result
            processing_time = time.time() - start_time
            logger.info(
                f"Query processing completed in {processing_time:.2f} seconds"
            )
            
            return QueryResult(
                answer=answer,
                processing_time_seconds=processing_time
            )
            
        except ValueError as e:
            error_msg = str(e)
            logger.error(f"Query processing failed - validation error: {error_msg}")
            answer = Answer(
                text=f"Error: {error_msg}",
                supporting_chunks=[],
                confidence="not_found"
            )
            processing_time = time.time() - start_time
            return QueryResult(
                answer=answer,
                processing_time_seconds=processing_time
            )
        
        except Exception as e:
            error_msg = f"Unexpected error during query processing: {str(e)}"
            logger.error(error_msg, exc_info=True)
            answer = Answer(
                text=f"Error: Could not process query. {str(e)}",
                supporting_chunks=[],
                confidence="not_found"
            )
            processing_time = time.time() - start_time
            return QueryResult(
                answer=answer,
                processing_time_seconds=processing_time
            )
    
    def validate_system_ready(self) -> bool:
        """
        Validate that the system is ready to process queries.
        
        Checks if the vector store has been initialized with embeddings.
        
        Returns:
            True if system is ready, False otherwise
        """
        try:
            index_size = self.vector_store.get_index_size()
            is_ready = index_size > 0
            
            if is_ready:
                logger.debug(f"System ready: {index_size} embeddings in vector store")
            else:
                logger.warning("System not ready: vector store is empty")
            
            return is_ready
        
        except Exception as e:
            logger.error(f"Error checking system readiness: {str(e)}")
            return False
    
    def load_index(self, index_path: Optional[str] = None) -> bool:
        """
        Load a previously saved vector index from disk.
        
        Args:
            index_path: Path to the saved index (uses self.index_path if not provided)
            
        Returns:
            True if index loaded successfully, False otherwise
        """
        path = index_path or self.index_path
        
        if not path:
            logger.error("Cannot load index: no index path provided")
            return False
        
        try:
            logger.info(f"Loading vector index from {path}...")
            self.vector_store.load_index(path)
            index_size = self.vector_store.get_index_size()
            logger.info(f"Index loaded successfully: {index_size} embeddings")
            return True
        
        except FileNotFoundError:
            logger.error(f"Index file not found at {path}")
            return False
        
        except Exception as e:
            logger.error(f"Failed to load index: {str(e)}", exc_info=True)
            return False
