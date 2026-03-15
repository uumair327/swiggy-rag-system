#!/bin/bash
# Pre-publish system test
# Verifies everything works before pushing to GitHub

echo "╔══════════════════════════════════════════════════════════════════════╗"
echo "║                                                                      ║"
echo "║              Pre-Publish System Test                                ║"
echo "║                                                                      ║"
echo "╚══════════════════════════════════════════════════════════════════════╝"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

TESTS_PASSED=0
TESTS_FAILED=0

# Test 1: Check Python version
echo "1️⃣  Checking Python version..."
if venv312/bin/python --version | grep -q "3.12"; then
    echo -e "${GREEN}✓${NC} Python 3.12 installed"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗${NC} Python 3.12 not found"
    ((TESTS_FAILED++))
fi
echo ""

# Test 2: Check virtual environment
echo "2️⃣  Checking virtual environment..."
if [ -d "venv312" ]; then
    echo -e "${GREEN}✓${NC} Virtual environment exists"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗${NC} Virtual environment not found"
    ((TESTS_FAILED++))
fi
echo ""

# Test 3: Check dependencies
echo "3️⃣  Checking dependencies..."
if venv312/bin/pip list | grep -q "pypdf"; then
    echo -e "${GREEN}✓${NC} Dependencies installed"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗${NC} Dependencies not installed"
    ((TESTS_FAILED++))
fi
echo ""

# Test 4: Check Ollama
echo "4️⃣  Checking Ollama..."
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Ollama is running"
    ((TESTS_PASSED++))
else
    echo -e "${YELLOW}⚠${NC}  Ollama is not running"
    echo "   Start with: ollama serve (in separate terminal)"
    ((TESTS_FAILED++))
fi
echo ""

# Test 5: Check llama3.2 model
echo "5️⃣  Checking llama3.2 model..."
if ollama list 2>/dev/null | grep -q "llama3.2"; then
    echo -e "${GREEN}✓${NC} llama3.2 model installed"
    ((TESTS_PASSED++))
else
    echo -e "${YELLOW}⚠${NC}  llama3.2 model not found"
    echo "   Install with: ollama pull llama3.2"
    ((TESTS_FAILED++))
fi
echo ""

# Test 6: Check vector index
echo "6️⃣  Checking vector index..."
if [ -f "data/vector_index.faiss.faiss" ]; then
    echo -e "${GREEN}✓${NC} Vector index exists"
    ((TESTS_PASSED++))
else
    echo -e "${YELLOW}⚠${NC}  Vector index not found (will be created on first ingest)"
    ((TESTS_PASSED++))
fi
echo ""

# Test 7: Check documentation
echo "7️⃣  Checking documentation..."
if [ -f "README.md" ] && [ -f "CONTRIBUTING.md" ] && [ -f "docs/ARCHITECTURE.md" ]; then
    echo -e "${GREEN}✓${NC} Documentation complete"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗${NC} Documentation incomplete"
    ((TESTS_FAILED++))
fi
echo ""

# Test 8: Check CI/CD
echo "8️⃣  Checking CI/CD configuration..."
if [ -f ".github/workflows/ci.yml" ] && [ -f ".github/workflows/release.yml" ]; then
    echo -e "${GREEN}✓${NC} CI/CD workflows configured"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗${NC} CI/CD workflows missing"
    ((TESTS_FAILED++))
fi
echo ""

# Test 9: Check Docker
echo "9️⃣  Checking Docker configuration..."
if [ -f "Dockerfile" ] && [ -f "docker-compose.yml" ]; then
    echo -e "${GREEN}✓${NC} Docker configuration present"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗${NC} Docker configuration missing"
    ((TESTS_FAILED++))
fi
echo ""

# Test 10: Check GitHub configuration
echo "🔟 Checking GitHub configuration..."
if grep -q "uumair327" README.md && grep -q "umairansari.in" README.md; then
    echo -e "${GREEN}✓${NC} GitHub configuration updated"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗${NC} GitHub configuration not updated"
    ((TESTS_FAILED++))
fi
echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "Tests Passed: ${GREEN}${TESTS_PASSED}/10${NC}"
echo -e "Tests Failed: ${RED}${TESTS_FAILED}/10${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed! Ready to publish to GitHub!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Create GitHub repository: https://github.com/new"
    echo "2. Configure secrets (PYPI_API_TOKEN, DOCKER_USERNAME, DOCKER_PASSWORD)"
    echo "3. Run: git add . && git commit -m 'feat: initial release v1.0.0'"
    echo "4. Run: git push -u origin main"
    echo "5. Run: git tag -a v1.0.0 -m 'Release v1.0.0' && git push origin v1.0.0"
    echo ""
    exit 0
elif [ $TESTS_FAILED -le 2 ]; then
    echo -e "${YELLOW}⚠️  Minor issues found. Review warnings above.${NC}"
    echo "You can still publish, but consider fixing warnings first."
    exit 0
else
    echo -e "${RED}❌ Critical issues found. Please fix before publishing.${NC}"
    exit 1
fi
