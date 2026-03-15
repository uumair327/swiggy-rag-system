# Swiggy RAG System - Usage Guide

## Quick Start

The system is ready to use with Ollama (free local LLM)!

### Run a Query

```bash
./run.sh query "What was Swiggy's total income in FY 2024?"
```

### Ingest a New Document

```bash
./run.sh ingest "path/to/document.pdf"
```

## Example Queries

Try these questions about the Swiggy Annual Report:

```bash
./run.sh query "What was the total income for the year ended March 31, 2024?"
./run.sh query "How many cities does Swiggy operate in?"
./run.sh query "What is Swiggy's mission?"
./run.sh query "When did Swiggy launch Instamart?"
./run.sh query "What was the net profit or loss in FY 2024?"
```

## How It Works

1. **Document Ingestion**: PDF is loaded, text extracted, split into 1000-char chunks with 200-char overlap
2. **Embedding Generation**: Each chunk is converted to a 384-dimensional vector using all-MiniLM-L6-v2
3. **Vector Storage**: Embeddings stored in FAISS index for fast similarity search
4. **Query Processing**: Your question is embedded, top 5 similar chunks retrieved
5. **Answer Generation**: Ollama (llama3.2) generates answer strictly from retrieved context

## System Architecture

- **Core**: Hexagonal architecture with clean separation of concerns
- **Embeddings**: sentence-transformers (all-MiniLM-L6-v2) - runs locally
- **Vector Store**: FAISS - fast similarity search
- **LLM**: Ollama (llama3.2) - completely free, runs locally
- **Anti-Hallucination**: Strict context-only answering

## Configuration

Edit `.env` to customize:

```bash
# LLM Provider (ollama or openai)
LLM_PROVIDER=ollama

# Model name
LLM_MODEL=llama3.2

# Retrieval settings
TOP_K_CHUNKS=5
SIMILARITY_THRESHOLD=0.3

# Chunking settings
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
```

## Troubleshooting

**"Could not connect to Ollama"**:
- Make sure Ollama is running: `ollama serve` (in separate terminal)
- Check if llama3.2 is downloaded: `ollama list`

**Slow responses**:
- First query is slower (model loading)
- Subsequent queries are faster
- Consider using smaller model or upgrading hardware

**"Not found" responses**:
- Try rephrasing your question
- Check if the information is actually in the document
- Lower SIMILARITY_THRESHOLD in .env for more lenient matching

## Performance

- Document ingestion: ~2 seconds for 170-page PDF
- Query processing: 3-5 seconds per query
- Index auto-loads on startup (no re-ingestion needed)
- 91% code coverage with comprehensive tests
