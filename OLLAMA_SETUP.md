# Ollama Setup Guide - Free Local LLM

Ollama lets you run LLMs locally on your Mac for free. No API keys needed!

## Installation

### Step 1: Install Ollama

```bash
# Using Homebrew (recommended)
brew install ollama
```

Or download from: https://ollama.com/download

### Step 2: Start Ollama Service

```bash
ollama serve
```

Keep this terminal open - Ollama needs to run in the background.

### Step 3: Pull a Model

Open a new terminal and run:

```bash
# Recommended: Llama 3.2 (3B parameters, fast and good quality)
ollama pull llama3.2

# Alternatives:
# ollama pull mistral      # 7B parameters, very capable
# ollama pull phi3         # 3.8B parameters, Microsoft model
# ollama pull gemma2       # 9B parameters, Google model
```

### Step 4: Verify Installation

```bash
ollama list
```

You should see your downloaded model listed.

## Running the Swiggy RAG System

Once Ollama is set up, just run:

```bash
python main.py
```

The system is already configured to use Ollama (see `.env` file).

## Usage

1. **Ingest the document**:
   ```
   ingest Annual-Report-FY-2023-24 (1) (1).pdf
   ```

2. **Ask questions**:
   ```
   query What was Swiggy's revenue in FY 2023-24?
   ```

## Switching Between Ollama and OpenAI

Edit `.env` file:

**For Ollama (free)**:
```bash
LLM_PROVIDER=ollama
LLM_MODEL=llama3.2
```

**For OpenAI (paid)**:
```bash
LLM_PROVIDER=openai
LLM_MODEL=gpt-3.5-turbo
OPENAI_API_KEY=sk-your-key-here
```

## Troubleshooting

**"Could not connect to Ollama"**:
- Make sure `ollama serve` is running in another terminal
- Check if port 11434 is available: `lsof -i :11434`

**Model not found**:
- Pull the model first: `ollama pull llama3.2`
- Check available models: `ollama list`

**Slow responses**:
- Llama 3.2 (3B) is fastest
- Larger models (7B+) are slower but more capable
- First query is slower (model loading)

## Model Recommendations

- **llama3.2** (3B): Fast, good for most questions ⭐ Recommended
- **mistral** (7B): Better quality, slightly slower
- **phi3** (3.8B): Good balance of speed and quality
