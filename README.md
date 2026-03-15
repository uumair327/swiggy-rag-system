# Swiggy RAG System

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code Coverage](https://img.shields.io/badge/coverage-91%25-brightgreen.svg)](htmlcov/index.html)
[![Tests](https://img.shields.io/badge/tests-201%20passed-success.svg)](tests/)

A production-ready Retrieval-Augmented Generation (RAG) system built with Hexagonal Architecture for answering questions from PDF documents with zero hallucination.

## Features

- 🏗️ **Hexagonal Architecture**: Clean separation of concerns with ports and adapters
- 🎯 **Anti-Hallucination**: Strict context-based answering prevents LLM hallucinations
- 🔄 **Component Replaceability**: Swap LLM, vector store, or embedding models without code changes
- 🆓 **Free & Local**: Runs completely offline with Ollama (no API keys required)
- ⚡ **Fast**: Query processing in 3-5 seconds, auto-loads indexed documents
- 🧪 **Well-Tested**: 91% code coverage with unit, integration, and property-based tests
- 📊 **Production-Ready**: Comprehensive logging, error handling, and monitoring

## Quick Start

### Prerequisites

- Python 3.12+
- [Ollama](https://ollama.com) (for local LLM)

### Installation

```bash
# Clone the repository
git clone https://github.com/uumair327/swiggy-rag-system.git
cd swiggy-rag-system

# Create virtual environment
python3.12 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Ollama (macOS)
brew install ollama

# Start Ollama service (in separate terminal)
ollama serve

# Pull the LLM model
ollama pull llama3.2
```

### Usage

```bash
# Ingest a PDF document
python main.py ingest path/to/document.pdf

# Ask questions
python main.py query "What was the total revenue in FY 2024?"
```

Or use the convenience script:

```bash
./run.sh ingest document.pdf
./run.sh query "Your question here"
```

## Web UI (GitHub Pages)

This repository includes a static frontend in [web/index.html](web/index.html) that can be
published with GitHub Pages. The UI provides:

- API health check
- PDF ingestion trigger
- Question/answer interface

### 1. Run the backend API locally (or deploy it)

```bash
# Install dependencies
pip install -r requirements.txt

# Recommended for local-first setup
export LLM_PROVIDER=ollama
export LLM_MODEL=llama3.2

# Start API server
uvicorn api_server:app --host 0.0.0.0 --port 8000
```

### 2. Open the UI

- Local static file: open [web/index.html](web/index.html) in browser
- GitHub Pages URL (after workflow deploy):
  `https://<your-username>.github.io/<repo-name>/`

### 3. Connect UI to API

In the UI, set `API Base URL` to your backend endpoint, for example:

- `http://localhost:8000` (local)
- `https://your-api.example.com` (cloud)

Note: GitHub Pages hosts static files only. Your Python API must run separately.

### GitHub Setup Checklist (Best Practices)

1. Enable GitHub Pages with source set to GitHub Actions.
2. Keep production deployment in a protected GitHub Environment named `production`.
3. Add Actions secrets:
  - `CLOUD_DEPLOY_HOOK_URL` (required for backend deploy workflow)
  - `API_HEALTHCHECK_URL` (optional but recommended)
4. Push to `main` to trigger:
  - [.github/workflows/ci.yml](.github/workflows/ci.yml)
  - [.github/workflows/pages.yml](.github/workflows/pages.yml)
  - [.github/workflows/deploy-api.yml](.github/workflows/deploy-api.yml) when backend files change

## Architecture

### Hexagonal Architecture (Ports & Adapters)

```
┌─────────────────────────────────────────────────────────────┐
│                     Adapters (External)                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │   CLI    │  │  PyPDF   │  │  FAISS   │  │  Ollama  │   │
│  │ Adapter  │  │ Adapter  │  │ Adapter  │  │  Adapter │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
├───────┼─────────────┼──────────────┼─────────────┼──────────┤
│  ┌────▼─────┐  ┌───▼──────┐  ┌───▼──────┐  ┌───▼──────┐   │
│  │   UI     │  │ Document │  │  Vector  │  │   LLM    │   │
│  │   Port   │  │   Port   │  │   Port   │  │   Port   │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
├─────────────────────────────────────────────────────────────┤
│                      Core Domain                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              RAG Orchestrator                         │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ Document │  │   Text   │  │ Context  │  │  Answer  │  │
│  │Processor │  │ Chunker  │  │Retriever │  │Generator │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Components

- **Core Domain**: Business logic isolated from external dependencies
- **Ports**: Interfaces defining contracts for external interactions
- **Adapters**: Implementations connecting to specific technologies

### Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| PDF Processing | pypdf | Extract text from PDF documents |
| Embeddings | sentence-transformers | Convert text to vectors (all-MiniLM-L6-v2) |
| Vector Store | FAISS | Fast similarity search |
| LLM | Ollama (llama3.2) | Generate answers from context |
| Testing | pytest + Hypothesis | Unit, integration, and property-based tests |

## Configuration

Create a `.env` file (or use `.env.example` as template):

```bash
# LLM Provider (ollama or openai)
LLM_PROVIDER=ollama
LLM_MODEL=llama3.2

# OpenAI (optional, if using openai provider)
# OPENAI_API_KEY=sk-your-key-here

# Retrieval Settings
TOP_K_CHUNKS=5
SIMILARITY_THRESHOLD=0.3

# Chunking Settings
CHUNK_SIZE=1000
CHUNK_OVERLAP=200

# Model Settings
EMBEDDING_MODEL=all-MiniLM-L6-v2
LLM_TEMPERATURE=0.0

# Storage Paths
VECTOR_INDEX_PATH=./data/vector_index.faiss
CHUNKS_METADATA_PATH=./data/chunks_metadata.json
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=core --cov=ports --cov=adapters --cov-report=html

# Run specific test categories
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
pytest -m property      # Property-based tests only
```

### Project Structure

```
swiggy-rag-system/
├── core/                   # Core domain logic
│   ├── answer_generator.py
│   ├── config.py
│   ├── context_retriever.py
│   ├── document_processor.py
│   ├── embedding_generator.py
│   ├── factory.py
│   ├── models.py
│   ├── query_handler.py
│   ├── rag_orchestrator.py
│   └── text_chunker.py
├── ports/                  # Interface definitions
│   ├── inbound.py
│   └── outbound.py
├── adapters/               # External integrations
│   ├── cli_adapter.py
│   ├── faiss_adapter.py
│   ├── langchain_adapter.py
│   ├── ollama_adapter.py
│   ├── pypdf_adapter.py
│   └── sentence_transformer_adapter.py
├── tests/                  # Test suite
│   ├── unit/
│   ├── integration/
│   └── property/
├── data/                   # Vector indices (gitignored)
├── main.py                 # Entry point
├── requirements.txt        # Dependencies
└── README.md              # This file
```

## API Reference

### CLI Commands

```bash
# Ingest a document
python main.py ingest <file_path>

# Query the system
python main.py query "<question>"
```

### Programmatic Usage

```python
from core.factory import create_rag_system

# Initialize the system
rag_system = create_rag_system()

# Ingest a document
result = rag_system.ingest_document("path/to/document.pdf")
print(f"Indexed {result.chunks_created} chunks")

# Query the system
query_result = rag_system.process_query("What is the revenue?")
print(f"Answer: {query_result.answer.text}")
print(f"Confidence: {query_result.answer.confidence}")
```

## Performance

- **Document Ingestion**: ~2 seconds for 170-page PDF
- **Query Processing**: 3-5 seconds per query
- **Index Loading**: < 1 second on startup
- **Memory Usage**: ~500MB with loaded models
- **Throughput**: 10+ concurrent queries supported

## Switching LLM Providers

### Using OpenAI

```bash
# Set environment variables
export LLM_PROVIDER=openai
export OPENAI_API_KEY=sk-your-key-here
export LLM_MODEL=gpt-3.5-turbo

# Or update .env file
```

### Using Other Ollama Models

```bash
# Pull a different model
ollama pull mistral
ollama pull phi3

# Update configuration
export LLM_MODEL=mistral
```

## Troubleshooting

### Common Issues

**"Could not connect to Ollama"**
- Ensure Ollama is running: `ollama serve`
- Check if model is downloaded: `ollama list`

**"Vector store not initialized"**
- Ingest a document first: `python main.py ingest document.pdf`

**Slow responses**
- First query is slower (model loading)
- Consider using a smaller model (llama3.2 is recommended)

**SSL Certificate errors**
- Install pip-system-certs: `pip install pip-system-certs`
- Or use Python 3.12 which has better SSL support

## Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Write tests for your changes
4. Ensure all tests pass (`pytest`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Code Style

- Follow PEP 8
- Use type hints
- Write docstrings for all public methods
- Maintain test coverage above 80%

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [Hexagonal Architecture](https://alistair.cockburn.us/hexagonal-architecture/) principles
- Inspired by Clean Architecture by Robert C. Martin
- Uses [sentence-transformers](https://www.sbert.net/) for embeddings
- Powered by [Ollama](https://ollama.com) for local LLM inference

## Citation

If you use this project in your research or work, please cite:

```bibtex
@software{swiggy_rag_system,
  title = {Swiggy RAG System: Production-Ready Retrieval-Augmented Generation},
  author = {Umair Ansari},
  year = {2024},
  url = {https://github.com/uumair327/swiggy-rag-system}
}
```

## Support

- 📧 Email: contact@umairansari.in
- 🐛 Issues: [GitHub Issues](https://github.com/uumair327/swiggy-rag-system/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/uumair327/swiggy-rag-system/discussions)

---

Made with ❤️ using Hexagonal Architecture
