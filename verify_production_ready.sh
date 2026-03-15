#!/bin/bash
# Production Readiness Verification Script

echo "=========================================="
echo "Production Readiness Verification"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check counter
CHECKS_PASSED=0
CHECKS_FAILED=0

check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✓${NC} $1 exists"
        ((CHECKS_PASSED++))
    else
        echo -e "${RED}✗${NC} $1 missing"
        ((CHECKS_FAILED++))
    fi
}

check_dir() {
    if [ -d "$1" ]; then
        echo -e "${GREEN}✓${NC} $1 exists"
        ((CHECKS_PASSED++))
    else
        echo -e "${RED}✗${NC} $1 missing"
        ((CHECKS_FAILED++))
    fi
}

echo "Checking Core Files..."
check_file "README.md"
check_file "LICENSE"
check_file "requirements.txt"
check_file "setup.py"
check_file "pyproject.toml"
check_file "main.py"
echo ""

echo "Checking Documentation..."
check_file "CONTRIBUTING.md"
check_file "CHANGELOG.md"
check_file "SECURITY.md"
check_file "USAGE.md"
check_file "QUICK_START.md"
check_file "OLLAMA_SETUP.md"
check_file "docs/ARCHITECTURE.md"
check_file "docs/DEPLOYMENT.md"
check_file "docs/API.md"
echo ""

echo "Checking Configuration..."
check_file ".gitignore"
check_file ".env.example"
check_file ".pre-commit-config.yaml"
check_file "Makefile"
echo ""

echo "Checking Docker..."
check_file "Dockerfile"
check_file "docker-compose.yml"
check_file ".dockerignore"
echo ""

echo "Checking CI/CD..."
check_file ".github/workflows/ci.yml"
check_file ".github/workflows/codeql.yml"
check_file ".github/workflows/release.yml"
check_file ".github/dependabot.yml"
check_file ".github/ISSUE_TEMPLATE/bug_report.md"
check_file ".github/ISSUE_TEMPLATE/feature_request.md"
check_file ".github/PULL_REQUEST_TEMPLATE.md"
echo ""

echo "Checking Core Modules..."
check_dir "core"
check_dir "ports"
check_dir "adapters"
check_dir "tests"
echo ""

echo "Checking Scripts..."
check_file "run.sh"
if [ -x "run.sh" ]; then
    echo -e "${GREEN}✓${NC} run.sh is executable"
    ((CHECKS_PASSED++))
else
    echo -e "${RED}✗${NC} run.sh is not executable"
    ((CHECKS_FAILED++))
fi
echo ""

echo "=========================================="
echo "Summary"
echo "=========================================="
echo -e "Checks Passed: ${GREEN}${CHECKS_PASSED}${NC}"
echo -e "Checks Failed: ${RED}${CHECKS_FAILED}${NC}"
echo ""

if [ $CHECKS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ Project is PRODUCTION READY!${NC}"
    exit 0
else
    echo -e "${RED}✗ Project has missing components${NC}"
    exit 1
fi
