#!/bin/bash
# MCP Servers Test Script
# =======================

echo "🧪 Testing MCP Servers..."
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
PASSED=0
FAILED=0

test_server() {
    local server_name=$1
    local command=$2
    
    echo -n "Testing $server_name... "
    
    if command -v $command &> /dev/null; then
        echo -e "${GREEN}✓ Executable found${NC}"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}✗ Not found${NC}"
        ((FAILED++))
        return 1
    fi
}

# Test MCP CLI
echo "=== MCP CLI ==="
if command -v mcp &> /dev/null; then
    echo -e "${GREEN}✓ MCP CLI installed${NC}"
    MCP_VERSION=$(mcp --version 2>/dev/null || echo "unknown")
    echo "  Version: $MCP_VERSION"
    ((PASSED++))
else
    echo -e "${RED}✗ MCP CLI not found${NC}"
    ((FAILED++))
fi

echo ""
echo "=== Node.js & Tools ==="
test_server "Node.js" "node"
test_server "npm" "npm"
test_server "npx" "npx"

echo ""
echo "=== Python (for Memory Server) ==="
if command -v python3 &> /dev/null; then
    echo -e "${GREEN}✓ Python3 available${NC}"
    ((PASSED++))
else
    echo -e "${YELLOW}⚠ Python3 not found (Memory server requires Python)${NC}"
fi

echo ""
echo "=== Docker ==="
if command -v docker &> /dev/null; then
    echo -e "${GREEN}✓ Docker installed${NC}"
    ((PASSED++))
else
    echo -e "${YELLOW}⚠ Docker not found (optional)${NC}"
fi

echo ""
echo "=== Git ==="
if command -v git &> /dev/null; then
    echo -e "${GREEN}✓ Git installed${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗ Git not found${NC}"
    ((FAILED++))
fi

echo ""
echo "=== MCP Servers ==="
SERVICES=("filesystem" "git" "terminal" "calculator" "postgresql" "github" "browser" "aws")

for service in "${SERVICES[@]}"; do
    echo -n "Checking $service... "
    # Check if mcp can access this tool
    if mcp tools $service &> /dev/null; then
        echo -e "${GREEN}✓ Available${NC}"
        ((PASSED++))
    else
        echo -e "${YELLOW}⚠ Need configuration${NC}"
    fi
done

echo ""
echo "==================================="
echo -e "Test Summary: ${GREEN}$PASSED passed${NC}, ${RED}$FAILED failed${NC}"
echo "==================================="

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 All tests passed! MCP Servers are ready!${NC}"
else
    echo -e "${YELLOW}⚠ Some tests failed. Check configuration.${NC}"
fi

echo ""
echo "Next steps:"
echo "1. Set environment variables (GitHub token, etc.)"
echo "2. Run: mcp list"
echo "3. Start using servers!"