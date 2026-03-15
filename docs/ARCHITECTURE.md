# Architecture Documentation

## Overview

The Swiggy RAG System follows **Hexagonal Architecture** (also known as Ports and Adapters) combined with **Clean Architecture** principles to ensure maintainability, testability, and component replaceability.

## Architectural Principles

### 1. Dependency Inversion
- Core domain logic has no dependencies on external frameworks
- All dependencies point inward toward the domain
- External systems depend on core, never the reverse

### 2. Separation of Concerns
- **Core**: Business logic and domain models
- **Ports**: Interface definitions
- **Adapters**: External system implementations

### 3. Component Replaceability
- Any adapter can be swapped without changing core logic
- LLM, vector store, and embedding models are interchangeable
- Enables easy testing with mocks

## Layer Structure

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

## Core Components

### RAG Orchestrator
**Responsibility**: Coordinates the complete RAG workflow

**Key Methods**:
- `ingest_document(file_path)`: Load and index documents
- `process_query(question)`: Answer questions from indexed documents

**Dependencies**: All core components + vector store port

### Document Processor
**Responsibility**: Load and validate PDF documents

**Dependencies**: DocumentLoaderPort

### Text Chunker
**Responsibility**: Split text into overlapping chunks with metadata

**Configuration**:
- Chunk size: 1000 characters (default)
- Overlap: 200 characters (default)
- Preserves sentence boundaries

### Embedding Generator
**Responsibility**: Convert text to vector embeddings

**Dependencies**: EmbeddingModelPort

**Model**: all-MiniLM-L6-v2 (384 dimensions)

### Query Handler
**Responsibility**: Process and validate user questions

**Dependencies**: EmbeddingGenerator

### Context Retriever
**Responsibility**: Find relevant document chunks

**Dependencies**: VectorStorePort

**Configuration**:
- Top-K: 5 chunks (default)
- Similarity threshold: 0.3 (default)

### Answer Generator
**Responsibility**: Generate answers with anti-hallucination

**Dependencies**: LLMPort

**Features**:
- Strict context-based answering
- Confidence scoring
- Context validation

## Ports (Interfaces)

### Inbound Ports
- **RAGServicePort**: Primary entry point for RAG operations

### Outbound Ports
- **DocumentLoaderPort**: PDF loading interface
- **EmbeddingModelPort**: Text embedding interface
- **VectorStorePort**: Vector storage and search interface
- **LLMPort**: Language model interface

## Adapters (Implementations)

### PyPDFAdapter
- **Implements**: DocumentLoaderPort
- **Technology**: pypdf library
- **Purpose**: Extract text from PDF files

### SentenceTransformerAdapter
- **Implements**: EmbeddingModelPort
- **Technology**: sentence-transformers
- **Model**: all-MiniLM-L6-v2
- **Purpose**: Generate text embeddings

### FAISSAdapter
- **Implements**: VectorStorePort
- **Technology**: FAISS (Facebook AI Similarity Search)
- **Purpose**: Fast similarity search and vector storage

### OllamaAdapter
- **Implements**: LLMPort
- **Technology**: Ollama local LLM
- **Purpose**: Generate answers locally without API keys

### LangChainAdapter
- **Implements**: LLMPort
- **Technology**: LangChain + OpenAI
- **Purpose**: Generate answers using OpenAI API

### CLIAdapter
- **Implements**: RAGServicePort (inbound)
- **Technology**: Python argparse
- **Purpose**: Command-line interface

## Data Flow

### Document Ingestion Flow
```
PDF File → DocumentProcessor → TextChunker → EmbeddingGenerator 
→ VectorStore → Persistence
```

### Query Processing Flow
```
Question → QueryHandler → EmbeddingGenerator → ContextRetriever 
→ VectorStore → AnswerGenerator → LLM → Answer
```

## Design Patterns

### 1. Dependency Injection
All components receive dependencies through constructor injection:
```python
def __init__(self, dependency: PortInterface):
    self.dependency = dependency
```

### 2. Factory Pattern
System initialization uses factory function:
```python
rag_system = create_rag_system()
```

### 3. Strategy Pattern
Different LLM providers can be swapped:
```python
if provider == "ollama":
    llm = OllamaAdapter()
else:
    llm = LangChainAdapter()
```

### 4. Repository Pattern
Vector store acts as repository for embeddings

## Anti-Hallucination Strategy

### 1. Context-Only Answering
System prompt enforces strict context-based responses

### 2. Context Validation
Validates that answers reference provided context

### 3. Confidence Scoring
- **High**: Strong similarity + context validation
- **Medium**: Moderate similarity + context validation
- **Low**: Weak similarity or no context validation
- **Not Found**: Insufficient context

### 4. Similarity Threshold
Filters out irrelevant chunks (default: 0.3)

## Scalability Considerations

### Horizontal Scaling
- Stateless design enables multiple instances
- Vector store can be distributed (future enhancement)

### Vertical Scaling
- Batch embedding generation
- Efficient vector search with FAISS
- Configurable chunk sizes

### Performance Optimizations
- Index persistence and auto-loading
- Batch processing for embeddings
- Similarity threshold filtering

## Security Architecture

### 1. Input Validation
- File path validation
- Question validation
- Size limits

### 2. Secrets Management
- Environment variables for API keys
- No secrets in logs
- No secrets in code

### 3. Isolation
- Non-root Docker user
- Sandboxed PDF processing
- Input sanitization

## Testing Strategy

### 1. Unit Tests
- Test components in isolation
- Mock external dependencies
- Fast execution

### 2. Integration Tests
- Test component interactions
- Use real dependencies
- End-to-end workflows

### 3. Property-Based Tests
- Test invariants with Hypothesis
- 100 iterations per property
- Edge case discovery

## Extension Points

### Adding New Document Formats
1. Implement DocumentLoaderPort
2. Register in factory
3. No core changes needed

### Adding New LLM Providers
1. Implement LLMPort
2. Add to factory
3. Configure via environment

### Adding New Vector Stores
1. Implement VectorStorePort
2. Update factory
3. No core changes needed

## Monitoring and Observability

### Logging
- Structured logging at all levels
- Component-level loggers
- Configurable log levels

### Metrics (Future)
- Query latency
- Embedding generation time
- Vector search performance
- LLM response time

### Tracing (Future)
- End-to-end request tracing
- Component-level spans
- Performance profiling

## Future Enhancements

1. **Multi-document support**: Query across multiple documents
2. **Streaming responses**: Real-time answer generation
3. **Caching**: Query and embedding caching
4. **Distributed vector store**: Scale to millions of documents
5. **Web UI**: Browser-based interface
6. **API server**: REST/GraphQL API
7. **Multi-language**: Support for non-English documents
