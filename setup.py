"""Setup configuration for Swiggy RAG System."""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    requirements = [
        line.strip()
        for line in requirements_file.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]

setup(
    name="swiggy-rag-system",
    version="1.0.0",
    author="Umair Ansari",
    author_email="contact@umairansari.in",
    description="Production-ready RAG system with Hexagonal Architecture",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/uumair327/swiggy-rag-system",
    project_urls={
        "Bug Tracker": "https://github.com/uumair327/swiggy-rag-system/issues",
        "Documentation": "https://github.com/uumair327/swiggy-rag-system#readme",
        "Source Code": "https://github.com/uumair327/swiggy-rag-system",
        "Changelog": "https://github.com/uumair327/swiggy-rag-system/blob/main/CHANGELOG.md",
    },
    packages=find_packages(exclude=["tests", "tests.*", "docs", ".kiro"]),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing :: Linguistic",
    ],
    python_requires=">=3.12",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=8.0.0",
            "pytest-cov>=4.1.0",
            "pytest-mock>=3.12.0",
            "hypothesis>=6.98.0",
            "black>=24.0.0",
            "flake8>=7.0.0",
            "mypy>=1.8.0",
            "pip-audit>=2.6.0",
        ],
        "openai": [
            "langchain-openai>=0.0.5",
            "openai>=1.10.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "swiggy-rag=main:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords=[
        "rag",
        "retrieval-augmented-generation",
        "llm",
        "nlp",
        "question-answering",
        "pdf",
        "embeddings",
        "vector-search",
        "hexagonal-architecture",
        "clean-architecture",
    ],
)
