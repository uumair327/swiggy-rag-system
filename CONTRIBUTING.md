# Contributing to Swiggy RAG System

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for all contributors.

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in [Issues](https://github.com/uumair327/swiggy-rag-system/issues)
2. If not, create a new issue with:
   - Clear title and description
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (OS, Python version, etc.)
   - Relevant logs or screenshots

### Suggesting Features

1. Check existing [Issues](https://github.com/uumair327/swiggy-rag-system/issues) and [Discussions](https://github.com/uumair327/swiggy-rag-system/discussions)
2. Create a new issue with:
   - Clear use case description
   - Proposed solution or API
   - Alternative approaches considered
   - Impact on existing functionality

### Pull Requests

1. **Fork the repository**
   ```bash
   git clone https://github.com/uumair327/swiggy-rag-system.git
   cd swiggy-rag-system
   ```

2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**
   - Follow the code style guidelines
   - Write or update tests
   - Update documentation

4. **Run tests**
   ```bash
   pytest
   pytest --cov=core --cov=ports --cov=adapters
   ```

5. **Commit your changes**
   ```bash
   git commit -m "feat: add amazing feature"
   ```
   
   Use conventional commits:
   - `feat:` New feature
   - `fix:` Bug fix
   - `docs:` Documentation changes
   - `test:` Test additions or changes
   - `refactor:` Code refactoring
   - `perf:` Performance improvements
   - `chore:` Maintenance tasks

6. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Open a Pull Request**
   - Provide a clear description
   - Reference related issues
   - Include screenshots if applicable

## Development Setup

### Prerequisites

- Python 3.12+
- Ollama (for local testing)
- Git

### Setup

```bash
# Clone your fork
git clone https://github.com/uumair327/swiggy-rag-system.git
cd swiggy-rag-system

# Create virtual environment
python3.12 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest pytest-cov pytest-mock hypothesis black flake8 mypy

# Run tests
pytest
```

## Code Style

### Python Style Guide

- Follow [PEP 8](https://pep8.org/)
- Use type hints for all function signatures
- Maximum line length: 100 characters
- Use docstrings for all public classes and methods

### Formatting

```bash
# Format code with black
black core/ ports/ adapters/ tests/

# Check with flake8
flake8 core/ ports/ adapters/ tests/

# Type checking with mypy
mypy core/ ports/ adapters/
```

### Documentation

- Write clear docstrings following Google style
- Update README.md for user-facing changes
- Add inline comments for complex logic
- Update CHANGELOG.md

### Example Docstring

```python
def process_query(self, question: str) -> QueryResult:
    """
    Process a user question and generate an answer.
    
    Args:
        question: User's natural language question
        
    Returns:
        QueryResult containing answer, confidence, and metadata
        
    Raises:
        ValueError: If question is empty or invalid
        RuntimeError: If vector store is not initialized
        
    Example:
        >>> result = rag.process_query("What is the revenue?")
        >>> print(result.answer.text)
    """
```

## Testing Guidelines

### Test Coverage

- Maintain minimum 80% code coverage
- Write tests for all new features
- Update tests for bug fixes

### Test Types

1. **Unit Tests** (`tests/unit/`)
   - Test individual components in isolation
   - Mock external dependencies
   - Fast execution

2. **Integration Tests** (`tests/integration/`)
   - Test component interactions
   - Use real dependencies where possible
   - Test end-to-end workflows

3. **Property Tests** (`tests/property/`)
   - Use Hypothesis for property-based testing
   - Test invariants and edge cases
   - Verify correctness properties

### Running Tests

```bash
# All tests
pytest

# Specific category
pytest -m unit
pytest -m integration
pytest -m property

# With coverage
pytest --cov=core --cov=ports --cov=adapters --cov-report=html

# Specific file
pytest tests/unit/test_rag_orchestrator.py

# Verbose output
pytest -v
```

## Architecture Guidelines

### Hexagonal Architecture

- **Core Domain**: No external dependencies
- **Ports**: Define interfaces only
- **Adapters**: Implement ports for specific technologies

### Adding New Components

1. **Core Component**
   ```python
   # core/new_component.py
   class NewComponent:
       def __init__(self, dependency: PortInterface):
           self.dependency = dependency
   ```

2. **Port Interface**
   ```python
   # ports/outbound.py
   class NewPort(ABC):
       @abstractmethod
       def operation(self) -> Result:
           pass
   ```

3. **Adapter Implementation**
   ```python
   # adapters/new_adapter.py
   class NewAdapter(NewPort):
       def operation(self) -> Result:
           # Implementation
           pass
   ```

4. **Tests**
   ```python
   # tests/unit/test_new_component.py
   def test_new_component():
       mock_port = Mock(spec=NewPort)
       component = NewComponent(mock_port)
       # Test logic
   ```

## Commit Message Guidelines

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

### Examples

```
feat(core): add support for multiple document formats

- Add PDF, DOCX, and TXT support
- Update document processor interface
- Add format detection logic

Closes #123
```

```
fix(adapters): resolve Ollama connection timeout

- Increase timeout to 60 seconds
- Add retry logic with exponential backoff
- Improve error messages

Fixes #456
```

## Review Process

### Pull Request Checklist

- [ ] Tests pass locally
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] No merge conflicts
- [ ] Commits are clean and descriptive

### Review Criteria

Reviewers will check:
- Code quality and readability
- Test coverage and quality
- Documentation completeness
- Architecture compliance
- Performance impact
- Security considerations

## Release Process

1. Update version in `__version__.py`
2. Update CHANGELOG.md
3. Create release branch
4. Run full test suite
5. Create GitHub release
6. Tag version

## Questions?

- Open a [Discussion](https://github.com/uumair327/swiggy-rag-system/discussions)
- Join our community chat
- Email: contact@umairansari.in

Thank you for contributing! 🎉
