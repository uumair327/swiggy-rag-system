"""Adapters layer - implementations connecting to external technologies."""

from adapters.pypdf_adapter import PyPDFAdapter
from adapters.sentence_transformer_adapter import SentenceTransformerAdapter
from adapters.faiss_adapter import FAISSAdapter
from adapters.langchain_adapter import LangChainLLMAdapter
from adapters.cli_adapter import CLIAdapter

__all__ = [
    "PyPDFAdapter",
    "SentenceTransformerAdapter",
    "FAISSAdapter",
    "LangChainLLMAdapter",
    "CLIAdapter",
]
