"""PyPDF adapter for loading and extracting text from PDF documents."""

import os
import logging
from pathlib import Path
from typing import Optional
import pypdf
from pypdf.errors import PdfReadError

from ports.outbound import DocumentLoaderPort


logger = logging.getLogger(__name__)


class PyPDFAdapter(DocumentLoaderPort):
    """
    Adapter for loading PDF documents using pypdf library.
    
    Implements DocumentLoaderPort to provide PDF text extraction capabilities
    while preserving paragraph structure and handling errors gracefully.
    """
    
    def load_pdf(self, file_path: str) -> str:
        """
        Load PDF and extract text content from all pages.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Extracted text content with preserved paragraph structure
            
        Raises:
            FileNotFoundError: If the file does not exist
            ValueError: If the file is corrupted or cannot be read
        """
        logger.info(f"PyPDFAdapter: Loading PDF from {file_path}")
        
        # Validate file exists
        if not self.validate_file(file_path):
            logger.error(f"PyPDFAdapter: File not found or not readable: {file_path}")
            raise FileNotFoundError(f"PDF file not found at path: {file_path}")
        
        try:
            # Load PDF using pypdf.PdfReader
            reader = pypdf.PdfReader(file_path)
            page_count = len(reader.pages)
            logger.info(f"PyPDFAdapter: PDF loaded with {page_count} pages")
            
            # Extract text from all pages
            extracted_text = []
            for page_num, page in enumerate(reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text:
                        # Preserve paragraph structure by keeping newlines
                        extracted_text.append(page_text)
                        logger.debug(
                            f"PyPDFAdapter: Extracted {len(page_text)} chars from page {page_num + 1}"
                        )
                except Exception as e:
                    # Log warning but continue with other pages
                    logger.warning(
                        f"PyPDFAdapter: Could not extract text from page {page_num + 1}: {str(e)}"
                    )
                    continue
            
            # Join pages with double newline to preserve document structure
            full_text = "\n\n".join(extracted_text)
            
            if not full_text.strip():
                logger.error("PyPDFAdapter: No text content extracted from PDF")
                raise ValueError("No text content could be extracted from the PDF")
            
            logger.info(
                f"PyPDFAdapter: Successfully extracted {len(full_text)} characters "
                f"from {len(extracted_text)} pages"
            )
            return full_text
            
        except PdfReadError as e:
            logger.error(f"PyPDFAdapter: PDF read error: {str(e)}", exc_info=True)
            raise ValueError(f"Could not process PDF file. The file may be corrupted: {str(e)}")
        except Exception as e:
            # Catch any other unexpected errors
            if isinstance(e, (FileNotFoundError, ValueError)):
                raise
            logger.error(f"PyPDFAdapter: Unexpected error reading PDF: {str(e)}", exc_info=True)
            raise ValueError(f"Error reading PDF file: {str(e)}")
    
    def validate_file(self, file_path: str) -> bool:
        """
        Check if file exists and is readable.
        
        Args:
            file_path: Path to the file to validate
            
        Returns:
            True if file exists and is readable, False otherwise
        """
        try:
            path = Path(file_path)
            
            # Check if file exists
            if not path.exists():
                return False
            
            # Check if it's a file (not a directory)
            if not path.is_file():
                return False
            
            # Check if file is readable
            if not os.access(file_path, os.R_OK):
                return False
            
            # Check if file has .pdf extension
            if path.suffix.lower() != '.pdf':
                return False
            
            return True
            
        except Exception:
            # If any error occurs during validation, return False
            return False
