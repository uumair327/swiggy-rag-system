"""Document Processor component for loading and processing PDF documents."""

import os
import logging
from datetime import datetime

from core.models import DocumentContent, ValidationResult
from ports.outbound import DocumentLoaderPort

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """
    Processes PDF documents by loading and extracting text content.

    This component follows Hexagonal Architecture principles by depending on
    DocumentLoaderPort interface rather than concrete implementations.
    """

    def __init__(self, document_loader_port: DocumentLoaderPort):
        """
        Initialize DocumentProcessor with a document loader.

        Args:
            document_loader_port: Implementation of DocumentLoaderPort for loading PDFs
        """
        self.document_loader = document_loader_port
        logger.info("DocumentProcessor initialized")

    def validate_file_path(self, file_path: str) -> ValidationResult:
        """
        Validate that a file path exists and is accessible.

        Args:
            file_path: Path to the file to validate

        Returns:
            ValidationResult indicating if the file is valid
        """
        logger.debug(f"Validating file path: {file_path}")

        if not file_path:
            logger.warning("File path validation failed: empty path")
            return ValidationResult(is_valid=False, error_message="File path cannot be empty")

        if not os.path.exists(file_path):
            logger.error(f"File path validation failed: file not found at {file_path}")
            return ValidationResult(
                is_valid=False, error_message=f"Error: PDF file not found at path: {file_path}"
            )

        if not os.path.isfile(file_path):
            logger.error(f"File path validation failed: path is not a file: {file_path}")
            return ValidationResult(
                is_valid=False, error_message=f"Error: Path is not a file: {file_path}"
            )

        if not file_path.lower().endswith(".pd"):
            logger.error(f"File path validation failed: not a PDF file: {file_path}")
            return ValidationResult(
                is_valid=False, error_message=f"Error: File is not a PDF: {file_path}"
            )

        # Use the document loader's validation method
        if not self.document_loader.validate_file(file_path):
            logger.error(f"File path validation failed: file not readable: {file_path}")
            return ValidationResult(
                is_valid=False, error_message=f"Error: File is not readable: {file_path}"
            )

        logger.debug(f"File path validation successful: {file_path}")
        return ValidationResult(is_valid=True)

    def load_document(self, file_path: str) -> DocumentContent:
        """
        Load a PDF document and extract its text content.

        This method validates the file path, loads the PDF using the injected
        DocumentLoaderPort, and returns a DocumentContent domain model with
        extracted text, metadata, and timestamp.

        Args:
            file_path: Path to the PDF file to load

        Returns:
            DocumentContent containing extracted text and metadata

        Raises:
            FileNotFoundError: If the file does not exist
            ValueError: If the file is corrupted or cannot be processed
        """
        logger.info(f"Loading document from: {file_path}")

        # Validate file path first
        validation_result = self.validate_file_path(file_path)
        if not validation_result.is_valid:
            logger.error(f"Document loading failed: {validation_result.error_message}")
            raise FileNotFoundError(validation_result.error_message)

        try:
            # Use the document loader port to load the PDF
            logger.debug("Extracting text from PDF...")
            extracted_text = self.document_loader.load_pdf(file_path)

            # Check if extracted text is empty
            if not extracted_text or not extracted_text.strip():
                error_msg = (
                    "Warning: No text content extracted from PDF. "
                    "The document may be empty or contain only images."
                )
                logger.error(f"Document loading failed: {error_msg}")
                raise ValueError(error_msg)

            # Count pages by attempting to get page count from the text
            # This is a simple heuristic - actual page count should come from the loader
            # For now, we'll estimate based on text length (rough approximation)
            page_count = self._estimate_page_count(extracted_text)

            # Create timestamp
            timestamp = datetime.now().isoformat()

            logger.info(
                f"Document loaded successfully: {page_count} pages, "
                f"{len(extracted_text)} characters extracted from {file_path}"
            )

            # Return DocumentContent domain model
            return DocumentContent(
                text=extracted_text,
                source_path=file_path,
                page_count=page_count,
                extraction_timestamp=timestamp,
            )

        except FileNotFoundError:
            # Re-raise file not found errors
            raise
        except ValueError:
            # Re-raise value errors (corrupted PDF, empty document)
            raise
        except Exception as e:
            # Catch any other exceptions and wrap them
            error_msg = (
                "Error: Could not process PDF file. The file may be corrupted. "
                f"Details: {str(e)}"
            )
            logger.error(f"Document loading failed: {error_msg}", exc_info=True)
            raise ValueError(error_msg)

    def _estimate_page_count(self, text: str) -> int:
        """
        Estimate the number of pages based on text length.

        This is a rough heuristic. A more accurate implementation would
        get the actual page count from the PDF loader.

        Args:
            text: Extracted text content

        Returns:
            Estimated number of pages
        """
        # Rough estimate: ~3000 characters per page
        # This is just a placeholder - actual implementation should get
        # page count from the PDF loader
        chars_per_page = 3000
        estimated_pages = max(1, len(text) // chars_per_page)
        return estimated_pages
