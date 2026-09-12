#!/bin/bash
# MCP Server Installation Script for Linux/macOS
# ===============================================

set -e

echo "🚀 Starting MCP Servers Installation..."
echo ""

# Check Node.js installation
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed!"
    echo "💡 Install with: brew install node (macOS) or sudo apt install nodejs (Linux)"
    exit 1
fi

echo "🟢 Node.js version: $(node --version)"
echo "🟢 npm version: $(npm --version)"

# Install MCP CLI globally
echo ""
echo "📦 Installing MCP CLI..."
if npm install -g @modelcontextprotocol/cli; then
    echo "✅ MCP CLI installed successfully"
else
    echo "❌ Failed to install MCP CLI"
    exit 1
fi

# Create MCP config directory
echo ""
echo "📂 Setting up MCP configuration..."
mkdir -p ~/.mcp
CONFIG_FILE="$HOME/.mcp/mcp.json"

# Check if config exists, if not create from our template
if [ ! -f "$CONFIG_FILE" ]; then
    echo "Using configuration template from workspace..."
    # You can copy from the workspace config if needed
fi

# Install servers based on OS
echo ""
echo "🔧 Installing MCP Servers..."

# Filesystem Server
echo "   - Installing Filesystem Server..."
mcp add filesystem "npx @modelcontextprotocol/server-filesystem ~/Documents" 2>/dev/null || \
    echo "Note: Filesystem server needs manual config"

# Git Server
echo "   - Installing Git Server..."
mcp add git "npx @modelcontextprotocol/server-git"

# Terminal Server
echo "   - Installing Terminal Server..."
mcp add terminal "npx @modelcontextprotocol/server-terminal"

# Calculator Server
echo "   - Installing Calculator Server..."
mcp add calculator "npx @modelcontextprotocol/server-calculator"

# PostgreSQL Server
echo "   - Installing PostgreSQL Server..."
mcp add postgresql "npx @modelcontextprotocol/server-postgres"

# Docker Server
echo "   - Installing Docker Server..."
if command -v docker &> /dev/null; then
    mcp add docker "npx @modelcontextprotocol/server-docker"
else
    echo "   ⚠️  Docker not found - skipping Docker server"
fi

# GitHub Server
echo "   - Installing GitHub Server..."
mcp add github "npx @modelcontextprotocol/server-github"

# Browser Server
echo "   - Installing Browser Server..."
mcp add browser "npx @modelcontextprotocol/server-browser"

# Memory Server (requires Python)
echo "   - Installing Memory Server..."
if command -v pip3 &> /dev/null; then
    pip3 install mcp-server-memory --quiet 2>/dev/null || \
        echo "Note: Could not install Python memory server"
    mcp add memory "python3 -m mcp_server_memory" 2>/dev/null || \
        echo "Note: Memory server needs manual setup"
else
    echo "   ⚠️  pip3 not found - skipping Memory server"
fi

# AWS Server
echo "   - Installing AWS Server..."
mcp add aws "npx @modelcontextprotocol/server-aws"

echo ""
echo "✅ Installation Complete!"
echo ""

# Verify installation
echo "Verifying MCP CLI..."
mcp --version

echo ""
echo "📋 Installed MCP Servers:"
mcp list

echo ""
echo "🎉 Done!"
echo ""
echo "📝 Next Steps:"
echo "   1. Export your API keys:"
echo "      export GITHUB_TOKEN=your_token"
echo "      export FIRECRAWL_API_KEY=your_key"
echo "      export AWS_ACCESS_KEY=your_key"
echo "   2. Test servers: mcp test <server-name>"
echo "   3. Start using with your AI agents!"