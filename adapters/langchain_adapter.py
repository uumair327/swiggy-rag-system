"""LangChain adapter for LLM interactions."""

import os
import logging
from typing import Optional

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from ports.outbound import LLMPort

logger = logging.getLogger(__name__)


class LangChainLLMAdapter(LLMPort):
    """
    Adapter for LangChain LLM integration.

    Implements LLMPort using LangChain's ChatOpenAI for answer generation
    with anti-hallucination measures.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "gpt-3.5-turbo",
        temperature: float = 0.0,
    ):
        """
        Initialize LangChain LLM adapter.

        Args:
            api_key: OpenAI API key (if None, loads from OPENAI_API_KEY env var)
            model_name: Name of the OpenAI model to use
            temperature: Temperature for response generation (0.0 for deterministic)

        Raises:
            ValueError: If API key is not provided and not found in environment
        """
        # Load API key from environment if not provided
        if api_key is None:
            api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            raise ValueError(
                "OpenAI API key not found. Set OPENAI_API_KEY environment variable "
                "or provide api_key parameter."
            )

        self._model_name = model_name
        self._temperature = temperature

        try:
            self.llm = ChatOpenAI(api_key=api_key, model_name=model_name, temperature=temperature)
            logger.info(f"Initialized LangChain LLM adapter with model: {model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize LangChain LLM: {e}")
            raise ValueError(f"Could not initialize LLM: {e}")

    def generate_answer(self, question: str, context: str, system_prompt: str) -> str:
        """
        Generate answer based on question and context.

        Args:
            question: User's question
            context: Retrieved context from documents
            system_prompt: System instructions for the LLM

        Returns:
            Generated answer text

        Raises:
            RuntimeError: If API call fails or rate limit is exceeded
        """
        try:
            # Construct messages with system prompt and user question
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Context:\n{context}\n\nQuestion: {question}"),
            ]

            logger.debug(f"Generating answer for question: {question[:100]}...")

            # Generate response
            response = self.llm.invoke(messages)
            answer = response.content

            logger.info(f"Successfully generated answer (length: {len(answer)} chars)")
            return answer

        except Exception as e:
            error_msg = str(e).lower()

            # Handle rate limiting
            if "rate" in error_msg or "quota" in error_msg:
                logger.error(f"Rate limit exceeded: {e}")
                raise RuntimeError("Rate limit exceeded. Please wait and try again.") from e

            # Handle other API failures
            logger.error(f"LLM API call failed: {e}")
            raise RuntimeError("Could not generate answer. Please try again.") from e

    def get_model_name(self) -> str:
        """
        Return the name of the LLM being used.

        Returns:
            String identifier of the model
        """
        return self._model_name
