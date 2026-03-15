.PHONY: help install test lint format clean run-tests coverage docs

help:
	@echo "Swiggy RAG System - Makefile Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install          Install dependencies"
	@echo "  make install-dev      Install development dependencies"
	@echo ""
	@echo "Testing:"
	@echo "  make test             Run all tests"
	@echo "  make test-unit        Run unit tests only"
	@echo "  make test-integration Run integration tests only"
	@echo "  make test-property    Run property-based tests only"
	@echo "  make coverage         Run tests with coverage report"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint             Run linters (flake8, mypy)"
	@echo "  make format           Format code with black"
	@echo "  make format-check     Check code formatting"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean            Remove build artifacts"
	@echo "  make clean-pyc        Remove Python file artifacts"
	@echo "  make clean-test       Remove test artifacts"
	@echo ""
	@echo "Running:"
	@echo "  make run-ingest FILE=path/to/file.pdf  Ingest a document"
	@echo "  make run-query QUERY='Your question'   Run a query"

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt
	pip install pytest pytest-cov pytest-mock hypothesis black flake8 mypy pip-audit

test:
	pytest -v

test-unit:
	pytest -v -m unit

test-integration:
	pytest -v -m integration

test-property:
	pytest -v -m property

coverage:
	pytest --cov=core --cov=ports --cov=adapters --cov-report=html --cov-report=term-missing
	@echo "Coverage report generated in htmlcov/index.html"

lint:
	flake8 core/ ports/ adapters/ tests/ --max-line-length=100 --exclude=venv,venv312
	mypy core/ ports/ adapters/ --ignore-missing-imports

format:
	black core/ ports/ adapters/ tests/ main.py --line-length=100

format-check:
	black core/ ports/ adapters/ tests/ main.py --line-length=100 --check

security:
	pip-audit
	@echo "Security audit complete"

clean: clean-pyc clean-test
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .hypothesis/
	rm -rf .mypy_cache/

clean-pyc:
	find . -type f -name '*.py[co]' -delete
	find . -type d -name '__pycache__' -delete

clean-test:
	rm -rf .pytest_cache/
	rm -rf .hypothesis/
	rm -rf htmlcov/
	rm -f .coverage
	rm -f *.log

run-ingest:
	@if [ -z "$(FILE)" ]; then \
		echo "Error: FILE parameter required. Usage: make run-ingest FILE=path/to/file.pdf"; \
		exit 1; \
	fi
	python main.py ingest $(FILE)

run-query:
	@if [ -z "$(QUERY)" ]; then \
		echo "Error: QUERY parameter required. Usage: make run-query QUERY='Your question'"; \
		exit 1; \
	fi
	python main.py query "$(QUERY)"

docs:
	@echo "Documentation is in README.md, CONTRIBUTING.md, and inline docstrings"

check-all: format-check lint test coverage security
	@echo "All checks passed!"

.DEFAULT_GOAL := help
