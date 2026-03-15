# Release Checklist

Use this checklist before publishing to GitHub and PyPI.

## Pre-Release Tasks

### Code Quality
- [x] All tests passing (201 passed, 7 skipped)
- [x] Code coverage ≥ 80% (currently 91%)
- [x] No security vulnerabilities
- [x] Type hints on all public APIs
- [x] Docstrings on all public functions/classes
- [x] Logging configured properly
- [x] Error handling comprehensive

### Documentation
- [x] README.md complete with badges
- [x] CONTRIBUTING.md with guidelines
- [x] CHANGELOG.md following Keep a Changelog
- [x] LICENSE file (MIT)
- [x] SECURITY.md with vulnerability reporting
- [x] USAGE.md with examples
- [x] QUICK_START.md for new users
- [x] OLLAMA_SETUP.md for LLM setup
- [x] docs/ARCHITECTURE.md detailed
- [x] docs/DEPLOYMENT.md multi-platform
- [x] docs/API.md programmatic usage
- [x] All code examples tested

### Configuration
- [x] .env.example template
- [x] .gitignore comprehensive
- [x] pyproject.toml configured
- [x] setup.py with metadata
- [x] requirements.txt pinned versions
- [x] Makefile with common commands
- [x] .pre-commit-config.yaml

### Docker
- [x] Dockerfile multi-stage build
- [x] docker-compose.yml working
- [x] .dockerignore optimized
- [x] Health checks configured
- [x] Non-root user
- [x] Volume mounts for data

### CI/CD
- [x] .github/workflows/ci.yml
- [x] .github/workflows/codeql.yml
- [x] .github/workflows/release.yml
- [x] .github/dependabot.yml
- [x] Issue templates
- [x] PR template

## GitHub Setup

### Repository Configuration
- [ ] Create GitHub repository
- [ ] Set repository description
- [ ] Add topics/tags (rag, llm, python, hexagonal-architecture)
- [ ] Enable Issues
- [ ] Enable Discussions
- [ ] Enable Wiki (optional)
- [ ] Set default branch to main

### Secrets Configuration
- [ ] Add PYPI_API_TOKEN secret
- [ ] Add DOCKERHUB_USERNAME secret
- [ ] Add DOCKERHUB_TOKEN secret

### Branch Protection
- [ ] Require pull request reviews
- [ ] Require status checks to pass
- [ ] Require branches to be up to date
- [ ] Include administrators

### Labels
- [ ] Create labels: bug, enhancement, documentation, good first issue, help wanted

## Update Placeholders

### In All Files
- [ ] Replace "uumair327" with actual GitHub username
- [ ] Replace "contact@umairansari.in" with actual email
- [ ] Replace "Umair Ansari" with actual name
- [ ] Update all GitHub URLs

### Specific Files to Update
- [ ] README.md - URLs and badges
- [ ] CONTRIBUTING.md - URLs
- [ ] setup.py - author info and URLs
- [ ] core/__version__.py - author info
- [ ] SECURITY.md - contact email
- [ ] docs/API.md - URLs
- [ ] docs/DEPLOYMENT.md - URLs
- [ ] OLLAMA_SETUP.md - issue URL
- [ ] .github/workflows/*.yml - Docker image names

## Version Management

### Version 1.0.0
- [ ] Update core/__version__.py to "1.0.0"
- [ ] Update setup.py version to "1.0.0"
- [ ] Update CHANGELOG.md with release date
- [ ] Create git tag: `git tag -a v1.0.0 -m "Release v1.0.0"`

## Testing Before Release

### Local Testing
- [ ] Run all tests: `pytest`
- [ ] Run with coverage: `pytest --cov`
- [ ] Test CLI: `./run.sh query "test"`
- [ ] Test ingestion: `./run.sh ingest document.pdf`
- [ ] Check logs for errors

### Docker Testing
- [ ] Build image: `docker build -t swiggy-rag-system .`
- [ ] Run compose: `docker-compose up`
- [ ] Test ingestion in Docker
- [ ] Test queries in Docker
- [ ] Check health status

### Documentation Testing
- [ ] All links work
- [ ] All code examples run
- [ ] All commands execute successfully
- [ ] README renders correctly on GitHub

## Release Process

### 1. Final Commit
```bash
git add .
git commit -m "chore: prepare for v1.0.0 release"
git push origin main
```

### 2. Create Tag
```bash
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
```

### 3. GitHub Release
- [ ] Go to GitHub Releases
- [ ] Create new release from v1.0.0 tag
- [ ] Add release notes from CHANGELOG.md
- [ ] Upload any additional assets
- [ ] Publish release

### 4. PyPI Release
```bash
# Build package
python -m build

# Upload to PyPI (done automatically by CI)
# Or manually: twine upload dist/*
```

### 5. Docker Hub
```bash
# Tag and push (done automatically by CI)
# Or manually:
docker tag swiggy-rag-system:latest uumair327/swiggy-rag-system:1.0.0
docker tag swiggy-rag-system:latest uumair327/swiggy-rag-system:latest
docker push uumair327/swiggy-rag-system:1.0.0
docker push uumair327/swiggy-rag-system:latest
```

## Post-Release Tasks

### Verification
- [ ] Verify PyPI package: `pip install swiggy-rag-system`
- [ ] Verify Docker image: `docker pull uumair327/swiggy-rag-system:1.0.0`
- [ ] Verify GitHub release appears
- [ ] Check CI/CD badges on README

### Announcements
- [ ] Post on GitHub Discussions
- [ ] Tweet about release (optional)
- [ ] Post on relevant forums/communities (optional)
- [ ] Update personal website/portfolio (optional)

### Monitoring
- [ ] Monitor GitHub Issues
- [ ] Monitor PyPI download stats
- [ ] Monitor Docker Hub pulls
- [ ] Respond to community feedback

## Maintenance

### Regular Tasks
- [ ] Review and merge Dependabot PRs
- [ ] Respond to issues within 48 hours
- [ ] Review PRs within 72 hours
- [ ] Update documentation as needed
- [ ] Release patches for critical bugs

### Version Updates
- Patch (1.0.x): Bug fixes, security updates
- Minor (1.x.0): New features, backward compatible
- Major (x.0.0): Breaking changes

## Rollback Plan

If issues are discovered after release:

1. **Critical Bug**: Release patch immediately
   ```bash
   git tag -a v1.0.1 -m "Hotfix: critical bug"
   git push origin v1.0.1
   ```

2. **Major Issue**: Yank from PyPI
   ```bash
   pip install twine
   twine upload --skip-existing dist/*
   # Contact PyPI support to yank version
   ```

3. **Communication**: 
   - Post issue on GitHub
   - Update README with warning
   - Notify users via Discussions

## Support Channels

After release, monitor:
- GitHub Issues
- GitHub Discussions
- Email (security@example.com)
- Social media mentions

---

**Last Updated**: March 15, 2026
**Next Release**: TBD
