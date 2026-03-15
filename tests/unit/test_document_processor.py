"""Unit tests for DocumentProcessor component."""

import pytest
from datetime import datetime
from unittest.mock import Mock

from core.document_processor import DocumentProcessor
from core.models import DocumentContent
from ports.outbound import DocumentLoaderPort


class TestDocumentProcessor:
    """Test suite for DocumentProcessor class."""

    @pytest.fixture
    def mock_loader(self):
        """Create a mock DocumentLoaderPort."""
        loader = Mock(spec=DocumentLoaderPort)
        return loader

    @pytest.fixture
    def processor(self, mock_loader):
        """Create a DocumentProcessor with mock loader."""
        return DocumentProcessor(mock_loader)

    def test_init_with_document_loader(self, mock_loader):
        """Test DocumentProcessor initialization with DocumentLoaderPort."""
        processor = DocumentProcessor(mock_loader)
        assert processor.document_loader == mock_loader

    def test_validate_file_path_empty_path(self, processor):
        """Test validation fails for empty file path."""
        result = processor.validate_file_path("")
        assert not result.is_valid
        assert "cannot be empty" in result.error_message

    def test_validate_file_path_file_not_found(self, processor, mock_loader):
        """Test validation fails when file does not exist."""
        mock_loader.validate_file.return_value = False
        result = processor.validate_file_path("/nonexistent/file.pdf")
        assert not result.is_valid
        assert "not found" in result.error_message

    def test_validate_file_path_not_pdf(self, processor, tmp_path):
        """Test validation fails for non-PDF files."""
        # Create a temporary non-PDF file
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        result = processor.validate_file_path(str(test_file))
        assert not result.is_valid
        assert "not a PDF" in result.error_message

    def test_validate_file_path_valid_pdf(self, processor, mock_loader, tmp_path):
        """Test validation succeeds for valid PDF file."""
        # Create a temporary PDF file
        test_file = tmp_path / "test.pdf"
        test_file.write_text("PDF content")

        mock_loader.validate_file.return_value = True

        result = processor.validate_file_path(str(test_file))
        assert result.is_valid
        assert result.error_message is None

    def test_load_document_file_not_found(self, processor, mock_loader):
        """Test load_document raises FileNotFoundError for missing file."""
        mock_loader.validate_file.return_value = False

        with pytest.raises(FileNotFoundError) as exc_info:
            processor.load_document("/nonexistent/file.pdf")

        assert "not found" in str(exc_info.value)

    def test_load_document_corrupted_pdf(self, processor, mock_loader, tmp_path):
        """Test load_document raises ValueError for corrupted PDF."""
        # Create a temporary PDF file
        test_file = tmp_path / "corrupted.pdf"
        test_file.write_text("corrupted")

        mock_loader.validate_file.return_value = True
        mock_loader.load_pdf.side_effect = Exception("PDF parsing error")

        with pytest.raises(ValueError) as exc_info:
            processor.load_document(str(test_file))

        assert "corrupted" in str(exc_info.value).lower()

    def test_load_document_empty_content(self, processor, mock_loader, tmp_path):
        """Test load_document raises ValueError for empty PDF content."""
        # Create a temporary PDF file
        test_file = tmp_path / "empty.pdf"
        test_file.write_text("empty")

        mock_loader.validate_file.return_value = True
        mock_loader.load_pdf.return_value = ""

        with pytest.raises(ValueError) as exc_info:
            processor.load_document(str(test_file))

        assert "No text content" in str(exc_info.value)

    def test_load_document_success(self, processor, mock_loader, tmp_path):
        """Test successful document loading and text extraction."""
        # Create a temporary PDF file
        test_file = tmp_path / "valid.pdf"
        test_file.write_text("valid pd")

        expected_text = "This is extracted text from the PDF.\n\nIt has multiple paragraphs."

        mock_loader.validate_file.return_value = True
        mock_loader.load_pdf.return_value = expected_text

        result = processor.load_document(str(test_file))

        assert isinstance(result, DocumentContent)
        assert result.text == expected_text
        assert result.source_path == str(test_file)
        assert result.page_count > 0
        assert result.extraction_timestamp is not None

        # Verify timestamp is valid ISO format
        datetime.fromisoformat(result.extraction_timestamp)

    def test_load_document_preserves_text_structure(self, processor, mock_loader, tmp_path):
        """Test that load_document preserves paragraph structure."""
        test_file = tmp_path / "structured.pdf"
        test_file.write_text("structured")

        # Text with paragraphs and sections
        expected_text = """Section 1: Introduction

This is the first paragraph of the introduction.

This is the second paragraph with more details.

Section 2: Main Content

Here is the main content of the document."""

        mock_loader.validate_file.return_value = True
        mock_loader.load_pdf.return_value = expected_text

        result = processor.load_document(str(test_file))

        assert result.text == expected_text
        assert "\n\n" in result.text  # Verify paragraph breaks are preserved

    def test_load_document_page_count_estimation(self, processor, mock_loader, tmp_path):
        """Test that page count is estimated based on text length."""
        test_file = tmp_path / "multipage.pdf"
        test_file.write_text("multipage")

        # Create text that should span multiple pages (~3000 chars per page)
        long_text = "A" * 10000  # Should be ~3-4 pages

        mock_loader.validate_file.return_value = True
        mock_loader.load_pdf.return_value = long_text

        result = processor.load_document(str(test_file))

        assert result.page_count >= 3
        assert result.page_count <= 4

    def test_load_document_minimum_page_count(self, processor, mock_loader, tmp_path):
        """Test that page count is at least 1 for short documents."""
        test_file = tmp_path / "short.pdf"
        test_file.write_text("short")

        short_text = "Short document"

        mock_loader.validate_file.return_value = True
        mock_loader.load_pdf.return_value = short_text

        result = processor.load_document(str(test_file))

        assert result.page_count >= 1

    def test_document_processor_uses_injected_loader(self, mock_loader, tmp_path):
        """Test that DocumentProcessor uses the injected DocumentLoaderPort."""
        test_file = tmp_path / "test.pdf"
        test_file.write_text("test")

        processor = DocumentProcessor(mock_loader)

        mock_loader.validate_file.return_value = True
        mock_loader.load_pdf.return_value = "Extracted text"

        result = processor.load_document(str(test_file))

        # Verify the mock loader was called
        mock_loader.validate_file.assert_called_once_with(str(test_file))
        mock_loader.load_pdf.assert_called_once_with(str(test_file))

        assert result.text == "Extracted text"
