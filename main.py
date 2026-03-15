#!/usr/bin/env python3
"""
Main entry point for the Swiggy RAG System.

This module initializes the RAG system with all dependencies and starts
the CLI interface for user interaction.
"""

import sys
import logging
from pathlib import Path

from core.factory import create_rag_system, ConfigurationError
from adapters.cli_adapter import CLIAdapter


def setup_logging() -> None:
    """Configure logging for the application."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('swiggy_rag.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )


def display_startup_banner() -> None:
    """Display startup banner with system information."""
    print("\n" + "="*70)
    print("SWIGGY RAG SYSTEM")
    print("="*70)
    print("\nRetrieval-Augmented Generation for Swiggy Annual Report")
    print("Architecture: Hexagonal (Ports and Adapters)")
    print("\nInitializing system...")


def display_configuration_info(orchestrator) -> None:
    """
    Display configuration information after successful initialization.
    
    Args:
        orchestrator: The initialized RAG orchestrator
    """
    print("\n" + "="*70)
    print("SYSTEM READY")
    print("="*70)
    print("\nConfiguration:")
    print("  - Embedding Model: all-MiniLM-L6-v2")
    print("  - LLM Model: gpt-3.5-turbo")
    print("  - Chunk Size: 1000 characters")
    print("  - Chunk Overlap: 200 characters")
    print("  - Top K Retrieval: 5 chunks")
    print("  - Similarity Threshold: 0.3")
    print("\nAvailable Commands:")
    print("  - ingest <file_path>  : Load and index a PDF document")
    print("  - query <question>    : Ask a question")
    print("\nFor help, use: python main.py --help")
    print("="*70 + "\n")


def main() -> int:
    """
    Main entry point for the Swiggy RAG System.
    
    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        # Setup logging
        setup_logging()
        logger = logging.getLogger(__name__)
        
        # Display startup banner
        display_startup_banner()
        
        # Create data directory if it doesn't exist
        data_dir = Path("./data")
        data_dir.mkdir(exist_ok=True)
        logger.info(f"Data directory: {data_dir.absolute()}")
        
        # Initialize RAG system using factory function
        logger.info("Creating RAG system...")
        rag_system = create_rag_system()
        
        # Display configuration info
        display_configuration_info(rag_system)
        
        # Create and start CLI adapter
        logger.info("Starting CLI adapter...")
        cli = CLIAdapter(rag_orchestrator=rag_system)
        
        # Run CLI with command-line arguments
        exit_code = cli.run()
        
        logger.info(f"Application exiting with code {exit_code}")
        return exit_code
    
    except ConfigurationError as e:
        print("\n" + "="*70, file=sys.stderr)
        print("CONFIGURATION ERROR", file=sys.stderr)
        print("="*70, file=sys.stderr)
        print(f"\n{str(e)}\n", file=sys.stderr)
        print("Please check your environment variables and try again.", file=sys.stderr)
        print("See .env.example for required configuration.\n", file=sys.stderr)
        print("="*70 + "\n", file=sys.stderr)
        return 1
    
    except KeyboardInterrupt:
        print("\n\nShutting down gracefully...")
        print("Goodbye!\n")
        return 0
    
    except Exception as e:
        print("\n" + "="*70, file=sys.stderr)
        print("UNEXPECTED ERROR", file=sys.stderr)
        print("="*70, file=sys.stderr)
        print(f"\n{str(e)}\n", file=sys.stderr)
        print("Please check the log file (swiggy_rag.log) for details.\n", file=sys.stderr)
        print("="*70 + "\n", file=sys.stderr)
        
        logger = logging.getLogger(__name__)
        logger.error("Unexpected error in main", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
