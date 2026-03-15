# GitHub Workflows

This directory contains CI/CD workflows for the Swiggy RAG System.

## Workflows

### CI Pipeline (`ci.yml`)

Runs on every push and pull request to main branch.

**Jobs**:
1. **Test** - Runs test suite on Python 3.12
2. **Lint** - Code quality checks (black, flake8, mypy)
3. **Security** - Security scanning (bandit, pip-audit)

**Triggers**:
- Push to main branch
- Pull requests to main branch

### CodeQL Analysis (`codeql.yml`)

Security vulnerability scanning using GitHub's CodeQL.

**Schedule**: Weekly on Mondays at 00:00 UTC

### Release Pipeline (`release.yml`)

Automated release process for new versions.

**Triggers**: Push of version tags (v*)

**Jobs**:
1. **Build** - Build Python package
2. **PyPI** - Publish to PyPI
3. **Docker** - Build and push Docker image
4. **GitHub Release** - Create GitHub release with artifacts

## Secrets Required

Configure these secrets in GitHub repository settings:

- `PYPI_API_TOKEN` - PyPI API token for package publishing
- `DOCKERHUB_USERNAME` - Docker Hub username
- `DOCKERHUB_TOKEN` - Docker Hub access token

## Badge URLs

Add these to README.md after first workflow run:

```markdown
[![CI](https://github.com/uumair327/swiggy-rag-system/workflows/CI/badge.svg)](https://github.com/uumair327/swiggy-rag-system/actions/workflows/ci.yml)
[![CodeQL](https://github.com/uumair327/swiggy-rag-system/workflows/CodeQL/badge.svg)](https://github.com/uumair327/swiggy-rag-system/actions/workflows/codeql.yml)
```

## Local Testing

Test workflows locally using [act](https://github.com/nektos/act):

```bash
# Install act
brew install act

# Run CI workflow
act -j test

# Run lint job
act -j lint
```
