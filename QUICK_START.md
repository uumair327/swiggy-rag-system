# Quick Start Guide

Get up and running with the Swiggy RAG System in 5 minutes.

## Prerequisites

- Python 3.12+
- 5GB disk space
- 8GB+ RAM

## Installation (5 steps)

### 1. Clone Repository

```bash
git clone https://github.com/uumair327/swiggy-rag-system.git
cd swiggy-rag-system
```

### 2. Create Virtual Environment

```bash
python3.12 -m venv venv312
source venv312/bin/activate  # On Windows: venv312\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Install Ollama

```bash
# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.com/install.sh | sh

# Windows: Download from https://ollama.com
```

### 5. Start Ollama & Pull Model

```bash
# Terminal 1: Start Ollama
ollama serve

# Terminal 2: Pull model
ollama pull llama3.2
```

## Usage

### Ingest a Document

```bash
./run.sh ingest document.pdf
```

### Ask Questions

```bash
./run.sh query "What was the total revenue?"
```

## Example Session

```bash
# Ingest the Swiggy Annual Report (already included)
./run.sh ingest "Annual-Report-FY-2023-24 (1) (1).pdf"

# Ask questions
./run.sh query "What was Swiggy's total income in FY 2024?"
./run.sh query "How many cities does Swiggy operate in?"
./run.sh query "What is Swiggy's mission?"
```

## Troubleshooting

### "Could not connect to Ollama"

Make sure Ollama is running:
```bash
ollama serve
```

### "Model not found"

Pull the model:
```bash
ollama pull llama3.2
```

### "Virtual environment not found"

Create it:
```bash
python3.12 -m venv venv312
source venv312/bin/activate
pip install -r requirements.txt
```

## Next Steps

- Read [USAGE.md](USAGE.md) for detailed usage
- Read [OLLAMA_SETUP.md](OLLAMA_SETUP.md) for Ollama configuration
- Read [docs/API.md](docs/API.md) for programmatic usage
- Read [CONTRIBUTING.md](CONTRIBUTING.md) to contribute

## Using OpenAI Instead

If you prefer OpenAI over Ollama:

```bash
# Edit .env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here
LLM_MODEL=gpt-3.5-turbo

# Run normally
./run.sh query "Your question"
```

## Docker Quick Start

```bash
# Start services
docker-compose up -d

# Pull model
docker exec swiggy-rag-ollama ollama pull llama3.2

# Ingest document
docker-compose run rag-system ingest /app/data/document.pdf

# Query
docker-compose run rag-system query "Your question"
```

## Support

- Issues: https://github.com/uumair327/swiggy-rag-system/issues
- Docs: https://github.com/uumair327/swiggy-rag-system#readme
