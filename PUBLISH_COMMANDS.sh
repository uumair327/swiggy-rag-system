#!/bin/bash
# Quick commands to publish Swiggy RAG System to GitHub
# Author: Umair Ansari
# Repository: https://github.com/uumair327/swiggy-rag-system

echo "╔══════════════════════════════════════════════════════════════════════╗"
echo "║                                                                      ║"
echo "║              Publishing Swiggy RAG System to GitHub                 ║"
echo "║                                                                      ║"
echo "╚══════════════════════════════════════════════════════════════════════╝"
echo ""

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "📦 Initializing git repository..."
    git init
    echo "✅ Git initialized"
else
    echo "✅ Git already initialized"
fi

# Check if remote exists
if git remote | grep -q "origin"; then
    echo "✅ Remote 'origin' already exists"
else
    echo "📡 Adding remote origin..."
    git remote add origin https://github.com/uumair327/swiggy-rag-system.git
    echo "✅ Remote added"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 Next Steps:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1️⃣  Create GitHub repository:"
echo "   → Go to: https://github.com/new"
echo "   → Name: swiggy-rag-system"
echo "   → Description: Production-ready RAG system with Hexagonal Architecture"
echo "   → Public repository"
echo "   → Don't initialize with README"
echo ""
echo "2️⃣  Configure GitHub secrets (Settings → Secrets → Actions):"
echo "   → PYPI_API_TOKEN (from https://pypi.org/manage/account/token/)"
echo "   → DOCKER_USERNAME (value: uumair327)"
echo "   → DOCKER_PASSWORD (from https://hub.docker.com/settings/security)"
echo ""
echo "3️⃣  Run these commands to push code:"
echo ""
echo "   git add ."
echo "   git commit -m \"feat: initial release v1.0.0"
echo ""
echo "   - Hexagonal Architecture implementation"
echo "   - Ollama and OpenAI LLM support"
echo "   - 91% test coverage with 201 tests"
echo "   - Comprehensive documentation"
echo "   - Docker deployment ready"
echo "   - Full CI/CD pipeline\""
echo ""
echo "   git branch -M main"
echo "   git push -u origin main"
echo ""
echo "4️⃣  Create release tag:"
echo ""
echo "   git tag -a v1.0.0 -m \"Release v1.0.0 - Initial production release\""
echo "   git push origin v1.0.0"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📚 Documentation:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "   📄 GITHUB_CONFIGURATION.md  - Complete configuration guide"
echo "   📄 NEXT_STEPS.md            - Detailed publishing steps"
echo "   📄 RELEASE_CHECKLIST.md     - Pre-release checklist"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Configuration Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Repository: https://github.com/uumair327/swiggy-rag-system"
echo "Author: Umair Ansari"
echo "Email: contact@umairansari.in"
echo ""
