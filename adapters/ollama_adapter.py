"""Ollama adapter for local LLM interactions."""

import logging
import requests  # type: ignore[import-untyped]

from ports.outbound import LLMPort

logger = logging.getLogger(__name__)


class OllamaAdapter(LLMPort):
    """
    Adapter for Ollama local LLM integration.

    Implements LLMPort using Ollama's local API for answer generation
    with anti-hallucination measures. No API key required.
    """

    def __init__(
        self,
        model_name: str = "llama3.2",
        base_url: str = "http://localhost:11434",
        temperature: float = 0.0,
    ):
        """
        Initialize Ollama LLM adapter.

        Args:
            model_name: Name of the Ollama model to use (e.g., llama3.2, mistral)
            base_url: Base URL for Ollama API
            temperature: Temperature for response generation (0.0 for deterministic)

        Raises:
            ValueError: If Ollama is not running or model is not available
        """
        self._model_name = model_name
        self._base_url = base_url.rstrip("/")
        self._temperature = temperature

        # Verify Ollama is running
        try:
            response = requests.get(f"{self._base_url}/api/tags", timeout=5)
            response.raise_for_status()
            logger.info(f"Connected to Ollama at {self._base_url}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to connect to Ollama: {e}")
            raise ValueError(
                f"Could not connect to Ollama at {self._base_url}. "
                "Make sure Ollama is running (brew install ollama && ollama serve)"
            ) from e

        logger.info(f"Initialized Ollama adapter with model: {model_name}")

    def generate_answer(self, question: str, context: str, system_prompt: str) -> str:
        """
        Generate answer based on question and context using Ollama.

        Args:
            question: User's question
            context: Retrieved context from documents
            system_prompt: System instructions for the LLM

        Returns:
            Generated answer text

        Raises:
            RuntimeError: If API call fails
        """
        try:
            # Construct prompt with system instructions and context
            full_prompt = f"{system_prompt}\n\nContext:\n{context}\n\nQuestion: {question}"

            logger.debug(f"Generating answer for question: {question[:100]}...")

            # Call Ollama API
            response = requests.post(
                f"{self._base_url}/api/generate",
                json={
                    "model": self._model_name,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {"temperature": self._temperature},
                },
                timeout=60,
            )
            response.raise_for_status()

            # Extract answer from response
            result = response.json()
            answer = result.get("response", "")

            logger.info(f"Successfully generated answer (length: {len(answer)} chars)")
            return answer

        except requests.exceptions.Timeout:
            logger.error("Ollama request timed out")
            raise RuntimeError("Request timed out. The model may be too slow or not responding.")

        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama API call failed: {e}")
            raise RuntimeError(f"Could not generate answer using Ollama: {str(e)}") from e

    def get_model_name(self) -> str:
        """
        Return the name of the LLM being used.

        Returns:
            String identifier of the model
        """
        return str(f"ollama/{self._model_name}")
