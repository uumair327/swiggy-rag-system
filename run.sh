#!/bin/bash
set -e

# Swiggy RAG System Runner
# Uses Python 3.12 with Ollama (free local LLM)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if virtual environment exists
if [ ! -d "venv312" ]; then
    echo -e "${RED}Error: Virtual environment not found at venv312/${NC}"
    echo "Please run: python3.12 -m venv venv312 && venv312/bin/pip install -r requirements.txt"
    exit 1
fi

# Check if Python exists in venv
if [ ! -f "venv312/bin/python" ]; then
    echo -e "${RED}Error: Python not found in virtual environment${NC}"
    exit 1
fi

# Load environment variables from .env if it exists
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
else
    echo -e "${YELLOW}Warning: .env file not found, using defaults${NC}"
fi

# Set default environment variables
export LLM_PROVIDER=${LLM_PROVIDER:-ollama}
export LLM_MODEL=${LLM_MODEL:-llama3.2}

# Check if Ollama is running (only if using Ollama provider)
if [ "$LLM_PROVIDER" = "ollama" ]; then
    if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo -e "${RED}Error: Ollama is not running${NC}"
        echo "Please start Ollama in another terminal: ollama serve"
        exit 1
    fi
fi

# Run the application
venv312/bin/python main.py "$@"
