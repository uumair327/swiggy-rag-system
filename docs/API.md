# API Documentation

## Programmatic API

### Installation

```bash
pip install swiggy-rag-system
```

### Quick Start

```python
from core.factory import create_rag_system

# Initialize system
rag = create_rag_system()

# Ingest document
result = rag.ingest_document("document.pdf")
print(f"Indexed {result.chunks_created} chunks")

# Query
query_result = rag.process_query("What is the revenue?")
print(f"Answer: {query_result.answer.text}")
print(f"Confidence: {query_result.answer.confidence}")
```

## Core API

### RAGOrchestrator

Main entry point for RAG operations.

#### `__init__()`

```python
def __init__(
    self,
    document_processor: DocumentProcessor,
    text_chunker: TextChunker,
    embedding_generator: EmbeddingGenerator,
    query_handler: QueryHandler,
    context_retriever: ContextRetriever,
    answer_generator: AnswerGenerator,
    vector_store: VectorStorePort
)
```

#### `ingest_document(file_path: str) -> IngestionResult`

Ingest and index a PDF document.

**Parameters**:
- `file_path` (str): Path to PDF file

**Returns**:
- `IngestionResult`: Contains chunks_created, processing_time, success status

**Raises**:
- `FileNotFoundError`: If file doesn't exist
- `ValueError`: If file is not a PDF

**Example**:
```python
result = rag.ingest_document("annual_report.pdf")
if result.success:
    print(f"Indexed {result.chunks_created} chunks in {result.processing_time:.2f}s")
```

#### `process_query(question: str) -> QueryResult`

Process a question and generate an answer.

**Parameters**:
- `question` (str): Natural language question

**Returns**:
- `QueryResult`: Contains answer, context, metadata

**Raises**:
- `ValueError`: If question is empty
- `RuntimeError`: If vector store not initialized

**Example**:
```python
result = rag.process_query("What was the total revenue?")
print(f"Answer: {result.answer.text}")
print(f"Confidence: {result.answer.confidence}")
print(f"Sources: {[c.metadata for c in result.context]}")
```

## Data Models

### Document

```python
@dataclass
class Document:
    content: str
    metadata: Dict[str, Any]
    source: str
```

### TextChunk

```python
@dataclass
class TextChunk:
    text: str
    metadata: ChunkMetadata
    embedding: Optional[List[float]] = None
```

### ChunkMetadata

```python
@dataclass
class ChunkMetadata:
    chunk_id: str
    source_document: str
    chunk_index: int
    start_char: int
    end_char: int
    total_chunks: int
```

### Query

```python
@dataclass
class Query:
    text: str
    embedding: Optional[List[float]] = None
    metadata: Optional[Dict[str, Any]] = None
```

### Answer

```python
@dataclass
class Answer:
    text: str
    confidence: AnswerConfidence
    context_used: List[str]
    metadata: Dict[str, Any]
```

### AnswerConfidence

```python
class AnswerConfidence(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NOT_FOUND = "not_found"
```

### QueryResult

```python
@dataclass
class QueryResult:
    query: Query
    answer: Answer
    context: List[TextChunk]
    processing_time: float
```

### IngestionResult

```python
@dataclass
class IngestionResult:
    success: bool
    chunks_created: int
    processing_time: float
    error_message: Optional[str] = None
```

## Configuration

### Environment Variables

```python
from core.config import Config

config = Config()

# Access configuration
print(config.llm_provider)  # "ollama" or "openai"
print(config.llm_model)     # "llama3.2"
print(config.top_k_chunks)  # 5
```

### Configuration Options

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `LLM_PROVIDER` | str | "ollama" | LLM provider (ollama/openai) |
| `LLM_MODEL` | str | "llama3.2" | Model name |
| `LLM_TEMPERATURE` | float | 0.0 | Temperature (0.0-1.0) |
| `OPENAI_API_KEY` | str | None | OpenAI API key |
| `OLLAMA_BASE_URL` | str | "http://localhost:11434" | Ollama URL |
| `TOP_K_CHUNKS` | int | 5 | Number of chunks to retrieve |
| `SIMILARITY_THRESHOLD` | float | 0.3 | Minimum similarity score |
| `CHUNK_SIZE` | int | 1000 | Characters per chunk |
| `CHUNK_OVERLAP` | int | 200 | Overlap between chunks |
| `EMBEDDING_MODEL` | str | "all-MiniLM-L6-v2" | Embedding model |
| `VECTOR_INDEX_PATH` | str | "./data/vector_index.faiss" | Index path |

## Advanced Usage

### Custom Configuration

```python
import os
from core.factory import create_rag_system

# Set custom configuration
os.environ["TOP_K_CHUNKS"] = "10"
os.environ["SIMILARITY_THRESHOLD"] = "0.5"

rag = create_rag_system()
```

### Using Different LLM Providers

#### Ollama (Local, Free)

```python
import os
os.environ["LLM_PROVIDER"] = "ollama"
os.environ["LLM_MODEL"] = "llama3.2"

rag = create_rag_system()
```

#### OpenAI

```python
import os
os.environ["LLM_PROVIDER"] = "openai"
os.environ["OPENAI_API_KEY"] = "sk-..."
os.environ["LLM_MODEL"] = "gpt-3.5-turbo"

rag = create_rag_system()
```

### Batch Processing

```python
from pathlib import Path

rag = create_rag_system()

# Ingest multiple documents
pdf_files = Path("documents/").glob("*.pdf")
for pdf_file in pdf_files:
    result = rag.ingest_document(str(pdf_file))
    print(f"Indexed {pdf_file.name}: {result.chunks_created} chunks")

# Query multiple questions
questions = [
    "What is the revenue?",
    "What are the key risks?",
    "Who is the CEO?"
]

for question in questions:
    result = rag.process_query(question)
    print(f"Q: {question}")
    print(f"A: {result.answer.text}\n")
```

### Error Handling

```python
from core.factory import create_rag_system

rag = create_rag_system()

try:
    result = rag.ingest_document("document.pdf")
    if not result.success:
        print(f"Ingestion failed: {result.error_message}")
except FileNotFoundError:
    print("File not found")
except ValueError as e:
    print(f"Invalid input: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")

try:
    query_result = rag.process_query("What is the revenue?")
    if query_result.answer.confidence == AnswerConfidence.NOT_FOUND:
        print("No relevant information found")
except ValueError as e:
    print(f"Invalid query: {e}")
except RuntimeError as e:
    print(f"System error: {e}")
```

### Custom Adapters

#### Implementing a Custom LLM Adapter

```python
from ports.outbound import LLMPort
from core.models import Answer, AnswerConfidence

class CustomLLMAdapter(LLMPort):
    def generate_answer(
        self,
        question: str,
        context: str,
        system_prompt: str
    ) -> Answer:
        # Your custom implementation
        response = your_llm_api.generate(
            prompt=f"{system_prompt}\n\nContext: {context}\n\nQuestion: {question}"
        )
        
        return Answer(
            text=response.text,
            confidence=AnswerConfidence.HIGH,
            context_used=[context],
            metadata={"model": "custom-model"}
        )
```

#### Using Custom Adapter

```python
from core.rag_orchestrator import RAGOrchestrator
from adapters.custom_llm_adapter import CustomLLMAdapter
# ... import other components

# Create custom LLM adapter
custom_llm = CustomLLMAdapter()

# Create RAG system with custom adapter
rag = RAGOrchestrator(
    document_processor=document_processor,
    text_chunker=text_chunker,
    embedding_generator=embedding_generator,
    query_handler=query_handler,
    context_retriever=context_retriever,
    answer_generator=AnswerGenerator(custom_llm),
    vector_store=vector_store
)
```

## CLI Reference

### Commands

#### `ingest`

Ingest a PDF document.

```bash
python main.py ingest <file_path>
```

**Options**:
- `file_path`: Path to PDF file (required)

**Example**:
```bash
python main.py ingest annual_report.pdf
```

#### `query`

Query the system.

```bash
python main.py query "<question>"
```

**Options**:
- `question`: Natural language question (required)

**Example**:
```bash
python main.py query "What was the total revenue in FY 2024?"
```

### Exit Codes

- `0`: Success
- `1`: General error
- `2`: File not found
- `3`: Invalid input
- `4`: System not initialized

## Testing

### Unit Testing

```python
from unittest.mock import Mock
from core.rag_orchestrator import RAGOrchestrator

def test_process_query():
    # Mock dependencies
    mock_query_handler = Mock()
    mock_context_retriever = Mock()
    mock_answer_generator = Mock()
    
    # Create orchestrator
    rag = RAGOrchestrator(
        document_processor=Mock(),
        text_chunker=Mock(),
        embedding_generator=Mock(),
        query_handler=mock_query_handler,
        context_retriever=mock_context_retriever,
        answer_generator=mock_answer_generator,
        vector_store=Mock()
    )
    
    # Test
    result = rag.process_query("test question")
    assert result is not None
```

## Performance

### Benchmarks

| Operation | Time | Memory |
|-----------|------|--------|
| Document ingestion (170 pages) | ~2s | ~300MB |
| Query processing | 3-5s | ~500MB |
| Index loading | <1s | ~100MB |

### Optimization Tips

1. **Reduce chunk size** for faster processing
2. **Lower top-K** for faster retrieval
3. **Use smaller models** for lower memory
4. **Batch queries** for better throughput

## Troubleshooting

### Common Issues

**"Vector store not initialized"**
```python
# Ingest a document first
rag.ingest_document("document.pdf")
```

**"Low confidence answers"**
```python
# Increase top-K or lower threshold
os.environ["TOP_K_CHUNKS"] = "10"
os.environ["SIMILARITY_THRESHOLD"] = "0.2"
```

**"Slow queries"**
```python
# Use smaller model
os.environ["LLM_MODEL"] = "llama3.2"
os.environ["TOP_K_CHUNKS"] = "3"
```

## Support

- Documentation: https://github.com/uumair327/swiggy-rag-system/docs
- Issues: https://github.com/uumair327/swiggy-rag-system/issues
- Email: support@example.com
