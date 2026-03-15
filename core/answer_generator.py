"""Answer Generator component for generating answers using LLM with anti-hallucination measures."""

import logging
from typing import List
from ports.outbound import LLMPort
from core.models import Answer, RetrievedChunk


logger = logging.getLogger(__name__)


class AnswerGenerator:
    """
    Generates answers using LLM with anti-hallucination measures.
    
    This component constructs prompts that enforce context-only answering,
    validates that answers reference the provided context, and returns
    structured Answer objects with confidence levels.
    """
    
    ANTI_HALLUCINATION_SYSTEM_PROMPT = """You are a helpful assistant that answers questions strictly based on the provided context.

Rules:
1. Only use information from the provided context to answer questions
2. If the context does not contain enough information to answer the question, respond with: "I could not find the answer in the document."
3. Do not use external knowledge or make assumptions
4. Quote relevant parts of the context when possible
5. Be concise and accurate"""
    
    NOT_FOUND_RESPONSE = "I could not find the answer in the document."
    
    def __init__(self, llm_port: LLMPort):
        """
        Initialize the AnswerGenerator with an LLM port.
        
        Args:
            llm_port: Implementation of LLMPort for generating answers
        """
        self.llm_port = llm_port
        logger.info(f"AnswerGenerator initialized with LLM: {llm_port.get_model_name()}")
    
    def generate_answer(
        self, 
        question: str, 
        context: List[RetrievedChunk]
    ) -> Answer:
        """
        Generate an answer based on the question and retrieved context.
        
        This method constructs an anti-hallucination prompt, calls the LLM,
        validates the answer, and returns a structured Answer object with
        confidence level.
        
        Args:
            question: User's question
            context: List of retrieved chunks with similarity scores
            
        Returns:
            Answer object with text, supporting chunks, and confidence level
        """
        logger.info(
            f"Generating answer for question: {question[:100]}... "
            f"with {len(context)} context chunks"
        )
        
        # Handle insufficient context
        if not context:
            logger.warning("No context provided for answer generation")
            return Answer(
                text=self.NOT_FOUND_RESPONSE,
                supporting_chunks=[],
                confidence="not_found"
            )
        
        # Prepare context string from retrieved chunks
        context_text = self._prepare_context_text(context)
        logger.debug(f"Prepared context text: {len(context_text)} characters")
        
        # Generate answer using LLM
        try:
            logger.debug("Calling LLM to generate answer...")
            answer_text = self.llm_port.generate_answer(
                question=question,
                context=context_text,
                system_prompt=self.ANTI_HALLUCINATION_SYSTEM_PROMPT
            )
            logger.info(f"LLM generated answer: {len(answer_text)} characters")
        except Exception as e:
            logger.error(f"Failed to generate answer with LLM: {str(e)}", exc_info=True)
            raise
        
        # Check if LLM returned "not found" response
        if self._is_not_found_response(answer_text):
            logger.info("LLM returned 'not found' response")
            return Answer(
                text=answer_text,
                supporting_chunks=context,
                confidence="not_found"
            )
        
        # Validate that answer references context
        references_context = self.validate_answer_from_context(answer_text, context)
        logger.debug(f"Answer references context: {references_context}")
        
        # Determine confidence level based on validation and similarity scores
        confidence = self._determine_confidence(context, references_context)
        logger.info(f"Answer generated with confidence: {confidence}")
        
        return Answer(
            text=answer_text,
            supporting_chunks=context,
            confidence=confidence
        )
    
    def validate_answer_from_context(
        self, 
        answer: str, 
        context: List[RetrievedChunk]
    ) -> bool:
        """
        Validate that the answer references the provided context.
        
        This method checks if the answer contains words or phrases from
        the context chunks, indicating that the answer is grounded in
        the provided context rather than hallucinated.
        
        Args:
            answer: Generated answer text
            context: List of retrieved chunks
            
        Returns:
            True if answer references context, False otherwise
        """
        if not context or not answer:
            return False
        
        # Normalize answer for comparison
        answer_lower = answer.lower()
        
        # Check if answer contains significant phrases from any context chunk
        for retrieved_chunk in context:
            chunk_text = retrieved_chunk.chunk.text.lower()
            
            # Extract meaningful phrases (3+ words) from chunk
            chunk_words = chunk_text.split()
            
            # Check for overlapping phrases of at least 3 consecutive words
            for i in range(len(chunk_words) - 2):
                phrase = " ".join(chunk_words[i:i+3])
                if phrase in answer_lower:
                    return True
        
        return False
    
    def _prepare_context_text(self, context: List[RetrievedChunk]) -> str:
        """
        Prepare context text from retrieved chunks.
        
        Args:
            context: List of retrieved chunks
            
        Returns:
            Formatted context string
        """
        context_parts = []
        for i, retrieved_chunk in enumerate(context, 1):
            chunk_text = retrieved_chunk.chunk.text
            similarity = retrieved_chunk.similarity_score
            context_parts.append(
                f"[Chunk {i}] (Similarity: {similarity:.3f})\n{chunk_text}"
            )
        
        return "\n\n".join(context_parts)
    
    def _is_not_found_response(self, answer_text: str) -> bool:
        """
        Check if the answer is a "not found" response.
        
        Args:
            answer_text: Generated answer text
            
        Returns:
            True if answer indicates information was not found
        """
        not_found_indicators = [
            "could not find",
            "cannot find",
            "not found",
            "no information",
            "insufficient information"
        ]
        
        answer_lower = answer_text.lower()
        return any(indicator in answer_lower for indicator in not_found_indicators)
    
    def _determine_confidence(
        self, 
        context: List[RetrievedChunk], 
        references_context: bool
    ) -> str:
        """
        Determine confidence level based on context quality and validation.
        
        Args:
            context: List of retrieved chunks
            references_context: Whether answer references context
            
        Returns:
            Confidence level: "high", "medium", "low", or "not_found"
        """
        if not context or not references_context:
            return "low"
        
        # Calculate average similarity score
        avg_similarity = sum(
            chunk.similarity_score for chunk in context
        ) / len(context)
        
        # Determine confidence based on similarity and validation
        if references_context and avg_similarity >= 0.7:
            return "high"
        elif references_context and avg_similarity >= 0.5:
            return "medium"
        else:
            return "low"
