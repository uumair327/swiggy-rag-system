"""CLI Adapter for the Swiggy RAG System."""

import argparse
import sys
import logging
from typing import Optional

from core.rag_orchestrator import RAGOrchestrator
from core.models import IngestionResult, QueryResult

logger = logging.getLogger(__name__)


class CLIAdapter:
    """
    Command-line interface adapter for the RAG system.

    Provides commands for:
    - ingest: Load and index PDF documents
    - query: Ask questions and receive answers

    This adapter implements the primary user interface following
    Hexagonal Architecture principles by depending on the RAGOrchestrator
    through the inbound port interface.
    """

    def __init__(self, rag_orchestrator: RAGOrchestrator):
        """
        Initialize CLI adapter with RAG orchestrator.

        Args:
            rag_orchestrator: The orchestrator that coordinates RAG operations
        """
        self.orchestrator = rag_orchestrator
        self.parser = self._create_parser()

    def _create_parser(self) -> argparse.ArgumentParser:
        """
        Create argument parser with all CLI commands.

        Returns:
            Configured ArgumentParser instance
        """
        parser = argparse.ArgumentParser(
            prog="swiggy-rag",
            description="Swiggy RAG System - Answer questions from PDF documents",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Ingest a PDF document
  swiggy-rag ingest path/to/document.pdf

  # Ask a question
  swiggy-rag query "What was the revenue in 2023?"

  # Load existing index and ask a question
  swiggy-rag query "What was the revenue in 2023?" --load-index path/to/index.faiss
            """,
        )

        subparsers = parser.add_subparsers(dest="command", help="Available commands", required=True)

        # Ingest command
        ingest_parser = subparsers.add_parser("ingest", help="Load and index a PDF document")
        ingest_parser.add_argument("file_path", type=str, help="Path to the PDF document to ingest")

        # Query command
        query_parser = subparsers.add_parser("query", help="Ask a question and receive an answer")
        query_parser.add_argument("question", type=str, help="Natural language question to answer")
        query_parser.add_argument(
            "--load-index",
            type=str,
            metavar="PATH",
            help="Load vector index from specified path before querying",
        )
        query_parser.add_argument(
            "--show-scores",
            action="store_true",
            help="Display similarity scores for supporting chunks",
        )

        return parser

    def run(self, args: Optional[list] = None) -> int:
        """
        Run the CLI with provided arguments.

        Args:
            args: Command-line arguments (uses sys.argv if None)

        Returns:
            Exit code (0 for success, 1 for error)
        """
        try:
            parsed_args = self.parser.parse_args(args)

            if parsed_args.command == "ingest":
                return self._handle_ingest(parsed_args.file_path)
            elif parsed_args.command == "query":
                return self._handle_query(
                    question=parsed_args.question,
                    load_index_path=getattr(parsed_args, "load_index", None),
                    show_scores=getattr(parsed_args, "show_scores", False),
                )
            else:
                self._display_error(f"Unknown command: {parsed_args.command}")
                return 1

        except KeyboardInterrupt:
            print("\n\nOperation cancelled by user.")
            return 0

        except Exception as e:
            self._display_error(f"Unexpected error: {str(e)}")
            logger.error("Unexpected error in CLI", exc_info=True)
            return 1

    def _handle_ingest(self, file_path: str) -> int:
        """
        Handle the ingest command.

        Args:
            file_path: Path to the PDF document to ingest

        Returns:
            Exit code (0 for success, 1 for error)
        """
        print(f"\n{'='*70}")
        print("DOCUMENT INGESTION")
        print(f"{'='*70}\n")
        print(f"Loading document: {file_path}")
        print("This may take a few moments...\n")

        result: IngestionResult = self.orchestrator.ingest_document(file_path)

        if result.success:
            self._display_ingestion_success(result)
            return 0
        else:
            self._display_ingestion_error(result)
            return 1

    def _handle_query(
        self, question: str, load_index_path: Optional[str] = None, show_scores: bool = False
    ) -> int:
        """
        Handle the query command.

        Args:
            question: User's natural language question
            load_index_path: Optional path to load vector index from
            show_scores: Whether to display similarity scores

        Returns:
            Exit code (0 for success, 1 for error)
        """
        # Load index if path provided
        if load_index_path:
            print(f"\nLoading vector index from: {load_index_path}")
            success = self.orchestrator.load_index(load_index_path)
            if not success:
                self._display_error(
                    f"Failed to load index from {load_index_path}. "
                    "Please check the path and try again."
                )
                return 1
            print("Index loaded successfully.\n")

        print(f"\n{'='*70}")
        print("QUERY PROCESSING")
        print(f"{'='*70}\n")
        print(f"Question: {question}\n")
        print("Processing query...\n")

        result: QueryResult = self.orchestrator.process_query(question)

        self._display_query_result(result, show_scores=show_scores)

        # Return error code if no answer found
        if not result.answer.has_answer():
            return 1

        return 0

    def _display_ingestion_success(self, result: IngestionResult) -> None:
        """
        Display successful ingestion result.

        Args:
            result: The ingestion result to display
        """
        print(f"{'='*70}")
        print("✓ INGESTION SUCCESSFUL")
        print(f"{'='*70}\n")
        print(f"  Chunks created:      {result.chunks_created}")
        print(f"  Embeddings stored:   {result.embeddings_stored}")
        print(f"\n{'='*70}\n")
        print("The document has been indexed and is ready for queries.")
        print("Use the 'query' command to ask questions.\n")

    def _display_ingestion_error(self, result: IngestionResult) -> None:
        """
        Display ingestion error.

        Args:
            result: The ingestion result with error information
        """
        print(f"{'='*70}")
        print("✗ INGESTION FAILED")
        print(f"{'='*70}\n")
        print(f"Error: {result.error_message}\n")
        print(f"{'='*70}\n")

    def _display_query_result(self, result: QueryResult, show_scores: bool = False) -> None:
        """
        Display query result with answer and supporting chunks.

        Args:
            result: The query result to display
            show_scores: Whether to display similarity scores
        """
        answer = result.answer

        print(f"{'='*70}")
        print("ANSWER")
        print(f"{'='*70}\n")

        # Display answer text
        print(answer.text)
        print()

        # Display confidence level
        confidence_display = {
            "high": "High ✓✓✓",
            "medium": "Medium ✓✓",
            "low": "Low ✓",
            "not_found": "Not Found ✗",
        }
        print(f"Confidence: {confidence_display.get(answer.confidence, answer.confidence)}")
        print(f"Processing Time: {result.processing_time_seconds:.2f} seconds")
        print()

        # Display supporting chunks if available
        if answer.supporting_chunks:
            print(f"{'='*70}")
            print(f"SUPPORTING CONTEXT ({len(answer.supporting_chunks)} chunks)")
            print(f"{'='*70}\n")

            for i, retrieved_chunk in enumerate(answer.supporting_chunks, 1):
                chunk = retrieved_chunk.chunk
                score = retrieved_chunk.similarity_score

                print(f"[Chunk {i}]")
                if show_scores:
                    print(f"Similarity Score: {score:.4f}")
                print(f"Source: {chunk.metadata.source_document}")
                print(f"Position: {chunk.metadata.start_position}-{chunk.metadata.end_position}")
                print()

                # Display chunk text with word wrapping
                chunk_text = chunk.text.strip()
                print(self._wrap_text(chunk_text, width=68))
                print()

                if i < len(answer.supporting_chunks):
                    print(f"{'-'*70}\n")

        print(f"{'='*70}\n")

    def _display_error(self, message: str) -> None:
        """
        Display error message with formatting.

        Args:
            message: Error message to display
        """
        print(f"\n{'='*70}", file=sys.stderr)
        print("ERROR", file=sys.stderr)
        print(f"{'='*70}\n", file=sys.stderr)
        print(message, file=sys.stderr)
        print(f"\n{'='*70}\n", file=sys.stderr)

    def _wrap_text(self, text: str, width: int = 70) -> str:
        """
        Wrap text to specified width while preserving words.

        Args:
            text: Text to wrap
            width: Maximum line width

        Returns:
            Wrapped text with newlines
        """
        words = text.split()
        lines = []
        current_line = []
        current_length = 0

        for word in words:
            word_length = len(word)

            # Check if adding this word would exceed width
            if current_length + word_length + len(current_line) > width:
                if current_line:
                    lines.append(" ".join(current_line))
                    current_line = [word]
                    current_length = word_length
                else:
                    # Single word longer than width
                    lines.append(word)
                    current_line = []
                    current_length = 0
            else:
                current_line.append(word)
                current_length += word_length

        # Add remaining words
        if current_line:
            lines.append(" ".join(current_line))

        return "\n".join(lines)


def main():
    """Main entry point for CLI when run as a script."""
    # This function is intentionally minimal - actual initialization
    # should be done in a separate main.py file that sets up logging,
    # creates the RAG system with all dependencies, and passes it to CLIAdapter
    print("Error: CLI adapter must be initialized with a RAG orchestrator.")
    print("Please use the main.py entry point instead.")
    sys.exit(1)


if __name__ == "__main__":
    main()
