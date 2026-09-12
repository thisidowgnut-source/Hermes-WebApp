# 🎯 MCP Server Installation Package

## 📦 What's Included

This package provides everything you need to install and manage MCP servers:

### Files Created:

| File | Purpose |
|------|---------|
| `MCP-Servers-CONFIG.json` | MCP configuration template (JSON format) |
| `README-MCP-Installation.md` | Complete installation guide |
| `install-mcp-servers.bat` | **Windows** batch installation script |
| `install-mcp-servers.sh` | **Linux/macOS** shell installation script |
| `test-mcp-servers.sh` | Test script for Linux/macOS |
| `Test-MCPServers.ps1` | **PowerShell** test script for Windows |
| `.env.mcp.example` | Environment variables template |

---

## 🚀 Quick Start

### Windows:
```powershell
1. Right-click install-mcp-servers.bat → "Run as Administrator"
2. Or run: .\install-mcp-servers.bat
```

### macOS/Linux:
```bash
chmod +x install-mcp-servers.sh
./install-mcp-servers.sh
```

---

## 📋 Servers Included

1. **Filesystem** - File system access
2. **Git** - Git repository operations
3. **Browser** - Web automation (Puppeteer)
4. **GitHub** - GitHub API integration
5. **PostgreSQL** - Database operations
6. **Docker** - Container management
7. **Terminal** - Command execution
8. **Calculator** - Math operations
9. **AWS** - AWS services
10. **Notion** - Notion workspace
11. **Memory** - Persistent storage
12. **Firecrawl** - Web scraping (requires API key)

---

## 🔧 Manual Configuration

After running the scripts, configure environment variables:

### Windows (PowerShell):
```powershell
# Copy template
Copy-Item .env.mcp.example .env

# Edit with your tokens
notepad .env

# Load variables
Get-Content .env | ForEach-Object {
    if ($_ -match "([^=]+)=(.*)") {
        [Environment]::SetEnvironmentVariable($matches[1], $matches[2], "User")
    }
}
```

### macOS/Linux:
```bash
# Copy template
cp .env.mcp.example .env

# Edit with your tokens
nano .env

# Load variables
source .env
```

---

## ✅ Verification

### Test all servers:
```bash
# Linux/macOS
./test-mcp-servers.sh

# Windows PowerShell
.\Test-MCPServers.ps1
```

### List installed servers:
```bash
mcp list
```

### Test individual server:
```bash
mcp test filesystem
mcp test git
```

---

## 🔐 Required API Keys

Before using these servers, get your API keys:

| Service | How to Get | Environment Variable |
|---------|-----------|---------------------|
| GitHub | Settings → Developer settings → Personal Access Tokens | GITHUB_TOKEN |
| Firecrawl | https://firecrawl.dev → Get API Key | FIRECRAWL_API_KEY |
| AWS | AWS Console → My Credentials | AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY |
| Notion | Settings → Integrations → Develop integrations | NOTION_KEY |

---

## 🛠️ Usage Examples

### Add server to config:
```bash
mcp add filesystem "npx @modelcontextprotocol/server-filesystem /workspace"
mcp add git "npx @modelcontextprotocol/server-git"
mcp add browser "npx @modelcontextprotocol/server-browser"
```

### Remove server:
```bash
mcp remove filesystem
```

### Update server:
```bash
mcp update filesystem
```

---

## 🚨 Troubleshooting

### "Command not found: mcp"
```bash
npm install -g @modelcontextprotocol/cli
echo $PATH  # Verify npm global bin is in PATH
```

### "Permission denied" errors
```bash
# macOS/Linux
sudo chown -R $(whoami) ~/.mcp
chmod 755 install-mcp-servers.sh
chmod 600 .env.mcp.example
```

### "Server not responding"
```bash
# Check Node version (needs 18+)
node --version

# Clear cache
npm cache clean --force
```

---

## 📚 Resources

- **Official Documentation**: https://modelcontextprotocol.io
- **GitHub**: https://github.com/modelcontextprotocol
- **MCP CLI**: https://www.npmjs.com/package/@modelcontextprotocol/cli
- **Servers Repo**: https://github.com/modelcontextprotocol/servers

---

## 🎉 Ready to Use!

Once installed and configured, you can:
1. Use in Claude Desktop
2. Use in Cursor IDE
3. Use in Windsurf
4. Use in VS Code with MCP extension

All MCP-capable agents will auto-discover these servers!