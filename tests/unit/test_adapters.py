"""Unit tests for all adapter implementations."""

import pytest
import os
import tempfile
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from adapters.pypdf_adapter import PyPDFAdapter
from adapters.sentence_transformer_adapter import SentenceTransformerAdapter
from adapters.faiss_adapter import FAISSAdapter
from adapters.langchain_adapter import LangChainLLMAdapter
from adapters.cli_adapter import CLIAdapter
from core.models import Chunk, ChunkMetadata, IngestionResult, QueryResult, Answer, RetrievedChunk
from core.rag_orchestrator import RAGOrchestrator


class TestPyPDFAdapter:
    """Test suite for PyPDFAdapter."""

    @pytest.fixture
    def adapter(self):
        """Create a PyPDFAdapter instance."""
        return PyPDFAdapter()

    def test_validate_file_exists(self, adapter, tmp_path):
        """Test file validation for existing PDF."""
        test_file = tmp_path / "test.pdf"
        test_file.write_text("PDF content")

        result = adapter.validate_file(str(test_file))

        assert result is True

    def test_validate_file_not_exists(self, adapter):
        """Test file validation for non-existent file."""
        result = adapter.validate_file("/nonexistent/file.pdf")

        assert result is False

    def test_validate_file_not_pdf(self, adapter, tmp_path):
        """Test file validation for non-PDF file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Text content")

        result = adapter.validate_file(str(test_file))

        assert result is False

    def test_validate_file_is_directory(self, adapter, tmp_path):
        """Test file validation for directory."""
        test_dir = tmp_path / "test_dir"
        test_dir.mkdir()

        result = adapter.validate_file(str(test_dir))

        assert result is False

    @patch("adapters.pypdf_adapter.pypdf.PdfReader")
    def test_load_pdf_success(self, mock_reader, adapter, tmp_path):
        """Test successful PDF loading."""
        test_file = tmp_path / "test.pdf"
        test_file.write_text("PDF")

        # Mock PDF reader
        mock_page1 = Mock()
        mock_page1.extract_text.return_value = "Page 1 text."
        mock_page2 = Mock()
        mock_page2.extract_text.return_value = "Page 2 text."

        mock_reader.return_value.pages = [mock_page1, mock_page2]

        result = adapter.load_pdf(str(test_file))

        assert "Page 1 text." in result
        assert "Page 2 text." in result

    def test_load_pdf_file_not_found(self, adapter):
        """Test PDF loading with non-existent file."""
        with pytest.raises(FileNotFoundError):
            adapter.load_pdf("/nonexistent/file.pdf")

    @patch("adapters.pypdf_adapter.pypdf.PdfReader")
    def test_load_pdf_corrupted(self, mock_reader, adapter, tmp_path):
        """Test PDF loading with corrupted file."""
        test_file = tmp_path / "corrupted.pdf"
        test_file.write_text("corrupted")

        from pypdf.errors import PdfReadError

        mock_reader.side_effect = PdfReadError("Corrupted")

        with pytest.raises(ValueError) as exc_info:
            adapter.load_pdf(str(test_file))

        assert "corrupted" in str(exc_info.value).lower()

    @patch("adapters.pypdf_adapter.pypdf.PdfReader")
    def test_load_pdf_empty_content(self, mock_reader, adapter, tmp_path):
        """Test PDF loading with no extractable text."""
        test_file = tmp_path / "empty.pdf"
        test_file.write_text("PDF")

        mock_page = Mock()
        mock_page.extract_text.return_value = ""
        mock_reader.return_value.pages = [mock_page]

        with pytest.raises(ValueError) as exc_info:
            adapter.load_pdf(str(test_file))

        assert "No text content" in str(exc_info.value)


class TestSentenceTransformerAdapter:
    """Test suite for SentenceTransformerAdapter."""

    @pytest.fixture
    def adapter(self):
        """Create a SentenceTransformerAdapter with mocked model."""
        with patch("adapters.sentence_transformer_adapter.SentenceTransformer") as mock_st:
            mock_model = Mock()
            mock_model.get_sentence_embedding_dimension.return_value = 384
            mock_st.return_value = mock_model

            adapter = SentenceTransformerAdapter("all-MiniLM-L6-v2")
            adapter.model = mock_model
            return adapter

    def test_init_with_model_name(self):
        """Test adapter initialization with model name."""
        with patch("adapters.sentence_transformer_adapter.SentenceTransformer") as mock_st:
            mock_model = Mock()
            mock_model.get_sentence_embedding_dimension.return_value = 384
            mock_st.return_value = mock_model

            adapter = SentenceTransformerAdapter("test-model")

            assert adapter.model_name == "test-model"
            mock_st.assert_called_once_with("test-model")

    def test_encode_single_text(self, adapter):
        """Test encoding single text."""
        adapter.model.encode.return_value = np.array([0.1, 0.2, 0.3])

        result = adapter.encode("Test text")

        assert isinstance(result, np.ndarray)
        assert len(result) == 3
        adapter.model.encode.assert_called_once()

    def test_encode_empty_text(self, adapter):
        """Test encoding empty text raises error."""
        with pytest.raises(ValueError) as exc_info:
            adapter.encode("")

        assert "empty text" in str(exc_info.value).lower()

    def test_encode_batch(self, adapter):
        """Test batch encoding."""
        adapter.model.encode.return_value = np.array([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]])

        result = adapter.encode_batch(["Text 1", "Text 2"])

        assert isinstance(result, np.ndarray)
        assert result.shape == (2, 3)

    def test_encode_batch_empty_list(self, adapter):
        """Test batch encoding with empty list."""
        with pytest.raises(ValueError):
            adapter.encode_batch([])

    def test_get_embedding_dimension(self, adapter):
        """Test getting embedding dimension."""
        dimension = adapter.get_embedding_dimension()

        assert dimension == 384


class TestFAISSAdapter:
    """Test suite for FAISSAdapter."""

    @pytest.fixture
    def adapter(self):
        """Create a FAISSAdapter instance."""
        return FAISSAdapter(dimension=384)

    @pytest.fixture
    def sample_chunks(self):
        """Create sample chunks."""
        return [
            Chunk(text="First chunk", metadata=ChunkMetadata(0, "test.pdf", 0, 11)),
            Chunk(text="Second chunk", metadata=ChunkMetadata(1, "test.pdf", 10, 22)),
        ]

    def test_init_with_dimension(self):
        """Test adapter initialization with dimension."""
        adapter = FAISSAdapter(dimension=512)

        assert adapter.dimension == 512
        assert adapter.index is not None
        assert len(adapter.chunks) == 0

    def test_add_embeddings(self, adapter, sample_chunks):
        """Test adding embeddings to index."""
        embeddings = np.random.rand(2, 384).astype(np.float32)

        adapter.add_embeddings(embeddings, sample_chunks)

        assert adapter.get_index_size() == 2
        assert len(adapter.chunks) == 2

    def test_add_embeddings_dimension_mismatch(self, adapter, sample_chunks):
        """Test adding embeddings with wrong dimension."""
        embeddings = np.random.rand(2, 256).astype(np.float32)  # Wrong dimension

        with pytest.raises(ValueError) as exc_info:
            adapter.add_embeddings(embeddings, sample_chunks)

        assert "dimension" in str(exc_info.value).lower()

    def test_add_embeddings_count_mismatch(self, adapter):
        """Test adding embeddings with mismatched chunk count."""
        embeddings = np.random.rand(2, 384).astype(np.float32)
        chunks = [Chunk(text="Only one", metadata=ChunkMetadata(0, "test.pdf", 0, 8))]

        with pytest.raises(ValueError) as exc_info:
            adapter.add_embeddings(embeddings, chunks)

        assert "must match" in str(exc_info.value).lower()

    def test_search(self, adapter, sample_chunks):
        """Test similarity search."""
        embeddings = np.random.rand(2, 384).astype(np.float32)
        adapter.add_embeddings(embeddings, sample_chunks)

        query = np.random.rand(384).astype(np.float32)
        results = adapter.search(query, top_k=2)

        assert len(results) <= 2
        assert all(isinstance(chunk, Chunk) for chunk, score in results)
        assert all(isinstance(score, float) for chunk, score in results)

    def test_search_empty_index(self, adapter):
        """Test search on empty index."""
        query = np.random.rand(384).astype(np.float32)
        results = adapter.search(query, top_k=5)

        assert len(results) == 0

    def test_save_and_load_index(self, adapter, sample_chunks, tmp_path):
        """Test saving and loading index."""
        embeddings = np.random.rand(2, 384).astype(np.float32)
        adapter.add_embeddings(embeddings, sample_chunks)

        index_path = tmp_path / "test_index"
        adapter.save_index(str(index_path))

        # Create new adapter and load
        new_adapter = FAISSAdapter(dimension=384)
        new_adapter.load_index(str(index_path))

        assert new_adapter.get_index_size() == 2
        assert len(new_adapter.chunks) == 2

    def test_load_index_file_not_found(self, adapter):
        """Test loading non-existent index."""
        with pytest.raises(FileNotFoundError):
            adapter.load_index("/nonexistent/index")

    def test_get_index_size(self, adapter, sample_chunks):
        """Test getting index size."""
        assert adapter.get_index_size() == 0

        embeddings = np.random.rand(2, 384).astype(np.float32)
        adapter.add_embeddings(embeddings, sample_chunks)

        assert adapter.get_index_size() == 2


class TestLangChainLLMAdapter:
    """Test suite for LangChainLLMAdapter."""

    @pytest.fixture
    def adapter(self):
        """Create a LangChainLLMAdapter with mocked LLM."""
        with patch("adapters.langchain_adapter.ChatOpenAI") as mock_llm:
            adapter = LangChainLLMAdapter(api_key="test-key", model_name="gpt-3.5-turbo")
            return adapter

    def test_init_with_api_key(self):
        """Test adapter initialization with API key."""
        with patch("adapters.langchain_adapter.ChatOpenAI") as mock_llm:
            adapter = LangChainLLMAdapter(api_key="test-key")

            assert adapter._model_name == "gpt-3.5-turbo"
            assert adapter._temperature == 0.0

    def test_init_without_api_key_from_env(self, monkeypatch):
        """Test adapter initialization with API key from environment."""
        monkeypatch.setenv("OPENAI_API_KEY", "env-api-key")

        with patch("adapters.langchain_adapter.ChatOpenAI") as mock_llm:
            adapter = LangChainLLMAdapter()

            mock_llm.assert_called_once()

    def test_init_without_api_key_raises_error(self, monkeypatch):
        """Test adapter initialization without API key raises error."""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        with pytest.raises(ValueError) as exc_info:
            LangChainLLMAdapter()

        assert "API key not found" in str(exc_info.value)

    def test_generate_answer_success(self, adapter):
        """Test successful answer generation."""
        mock_response = Mock()
        mock_response.content = "This is the answer."
        adapter.llm.invoke = Mock(return_value=mock_response)

        result = adapter.generate_answer(
            question="What is the revenue?",
            context="The revenue was $100M.",
            system_prompt="Answer from context only.",
        )

        assert result == "This is the answer."
        adapter.llm.invoke.assert_called_once()

    def test_generate_answer_rate_limit(self, adapter):
        """Test handling of rate limit errors."""
        adapter.llm.invoke = Mock(side_effect=Exception("Rate limit exceeded"))

        with pytest.raises(RuntimeError) as exc_info:
            adapter.generate_answer("Question", "Context", "Prompt")

        assert "Rate limit" in str(exc_info.value)

    def test_generate_answer_api_failure(self, adapter):
        """Test handling of API failures."""
        adapter.llm.invoke = Mock(side_effect=Exception("API error"))

        with pytest.raises(RuntimeError) as exc_info:
            adapter.generate_answer("Question", "Context", "Prompt")

        assert "Could not generate answer" in str(exc_info.value)

    def test_get_model_name(self, adapter):
        """Test getting model name."""
        model_name = adapter.get_model_name()

        assert model_name == "gpt-3.5-turbo"


class TestCLIAdapter:
    """Test suite for CLIAdapter."""

    @pytest.fixture
    def mock_orchestrator(self):
        """Create a mock RAGOrchestrator."""
        return Mock(spec=RAGOrchestrator)

    @pytest.fixture
    def cli(self, mock_orchestrator):
        """Create a CLIAdapter with mock orchestrator."""
        return CLIAdapter(mock_orchestrator)

    def test_init_with_orchestrator(self, mock_orchestrator):
        """Test CLI adapter initialization."""
        cli = CLIAdapter(mock_orchestrator)

        assert cli.orchestrator == mock_orchestrator
        assert cli.parser is not None

    def test_ingest_command_success(self, cli, mock_orchestrator):
        """Test successful ingest command."""
        mock_orchestrator.ingest_document.return_value = IngestionResult(
            success=True, chunks_created=10, embeddings_stored=10, error_message=None
        )

        exit_code = cli.run(["ingest", "test.pdf"])

        assert exit_code == 0
        mock_orchestrator.ingest_document.assert_called_once_with("test.pdf")

    def test_ingest_command_failure(self, cli, mock_orchestrator):
        """Test failed ingest command."""
        mock_orchestrator.ingest_document.return_value = IngestionResult(
            success=False, chunks_created=0, embeddings_stored=0, error_message="File not found"
        )

        exit_code = cli.run(["ingest", "missing.pdf"])

        assert exit_code == 1

    def test_query_command_success(self, cli, mock_orchestrator):
        """Test successful query command."""
        answer = Answer(text="The revenue was $100M.", supporting_chunks=[], confidence="high")
        mock_orchestrator.process_query.return_value = QueryResult(
            answer=answer, processing_time_seconds=1.5
        )

        exit_code = cli.run(["query", "What is the revenue?"])

        assert exit_code == 0
        mock_orchestrator.process_query.assert_called_once_with("What is the revenue?")

    def test_query_command_not_found(self, cli, mock_orchestrator):
        """Test query command with not found answer."""
        answer = Answer(
            text="I could not find the answer in the document.",
            supporting_chunks=[],
            confidence="not_found",
        )
        mock_orchestrator.process_query.return_value = QueryResult(
            answer=answer, processing_time_seconds=1.0
        )

        exit_code = cli.run(["query", "Unknown question?"])

        assert exit_code == 1

    def test_query_command_with_load_index(self, cli, mock_orchestrator):
        """Test query command with index loading."""
        mock_orchestrator.load_index.return_value = True
        answer = Answer(text="Answer", supporting_chunks=[], confidence="high")
        mock_orchestrator.process_query.return_value = QueryResult(
            answer=answer, processing_time_seconds=1.0
        )

        exit_code = cli.run(["query", "Question?", "--load-index", "./index.faiss"])

        assert exit_code == 0
        mock_orchestrator.load_index.assert_called_once_with("./index.faiss")

    def test_invalid_command(self, cli):
        """Test handling of invalid command."""
        with pytest.raises(SystemExit):
            cli.run(["invalid"])

    def test_keyboard_interrupt(self, cli, mock_orchestrator):
        """Test handling of keyboard interrupt."""
        mock_orchestrator.ingest_document.side_effect = KeyboardInterrupt()

        exit_code = cli.run(["ingest", "test.pdf"])

        assert exit_code == 0
