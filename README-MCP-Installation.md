# MCP Servers Installation Guide

## 📦 Requirements
- Node.js 18+
- npm or yarn
- Git
- (Optional) Python 3.8+ for memory server

## 🚀 Quick Install

```bash
# 1. Install MCP CLI globally
npm install -g @modelcontextprotocol/cli

# 2. Download config
curl -o .mcp.json https://raw.githubusercontent.com/your-repo/MCP-Servers-CONFIG.json

# 3. Verify installation
mcp list
```

## 📋 Individual Server Install

### Filesystem (Essential)
```bash
mcp add filesystem "npx @modelcontextprotocol/server-filesystem /workspace"
```

### Git
```bash
mcp add git "npx @modelcontextprotocol/server-git"
```

### Browser Automation
```bash
# Download browser-server.js from official repo
curl -o browser-server.js https://raw.githubusercontent.com/modelcontextprotocol/servers/main/src/browser.js
mcp add browser "node ./browser-server.js"
```

### GitHub Integration
```bash
mcp add github "npx @modelcontextprotocol/server-github"
# Set GITHUB_TOKEN in your environment
```

### PostgreSQL
```bash
mcp add postgresql "npx @modelcontextprotocol/server-postgres"
# Set PG_CONNECTION_STRING in your environment
```

### Docker
```bash
mcp add docker "npx @modelcontextprotocol/server-docker"
# Ensure Docker daemon running
```

### Terminal
```bash
mcp add terminal "npx @modelcontextprotocol/server-terminal"
```

### Firecrawl (Web Scraping)
```bash
mcp add firecrawl "npx @firecrawl/mcp-server"
# Set FIRECRAWL_API_KEY in your environment
```

### Memory (Persistent Storage)
```bash
pip install mcp-server-memory
mcp add memory "python -m mcp_server_memory"
```

### Calculator
```bash
mcp add calculator "npx @modelcontextprotocol/server-calculator"
```

### AWS
```bash
mcp add aws "npx @modelcontextprotocol/server-aws"
# Set AWS credentials in environment
```

## 🧪 Test All Servers

```bash
# Test filesystem
mcp test filesystem

# Test git
mcp test git

# Test all
for server in $(mcp list | awk 'NR>1 {print $1}'); do
  echo "Testing $server..."
  mcp test $server
done
```

## 🛠️ Environment Variables Setup

Create `.env` file:
```env
GITHUB_TOKEN=your_github_token
PG_CONNECTION_STRING=postgresql://user:pass@localhost/db
FIRECRAWL_API_KEY=your_api_key
AWS_ACCESS_KEY=your_key
AWS_SECRET=your_secret
NOTION_KEY=your_integration_token
```

Load environment:
```bash
# Linux/Mac
source .env

# Windows PowerShell
Get-Content .env | ForEach-Object {
    if ($_ -match "([^=]+)=(.*)") {
        [Environment]::SetEnvironmentVariable($matches[1], $matches[2])
    }
}
```

## 🐳 Docker Compose Setup (Optional)

```yaml
version: '3.8'
services:
  mcp-server:
    image: mcp/server:latest
    volumes:
      - ./.mcp.json:/app/.mcp.json
      - /workspace:/workspace
    environment:
      - GITHUB_TOKEN
      - PG_CONNECTION_STRING
    ports:
      - "3080:3080"
```

## 📊 Verification Commands

```bash
# List all servers
mcp list

# Check server status
mcp status

# Get server tools
mcp tools filesystem

# Test connection
mcp ping filesystem
```

## 🚨 Troubleshooting

### Server not starting
- Check Node.js version: `node --version` (should be 18+)
- Check npm: `npm --version`
- Check MCP CLI: `mcp --version`

### Permission denied
- Use `npx` with `sudo` carefully (not recommended)
- Check file permissions: `chmod +x`

### Environment issues
- Use `.env` file for secrets
- Never commit `.env` to git
- Use `.env.example` for team sharing

## 🤝 Support

- Official docs: https://modelcontextprotocol.io
- GitHub: https://github.com/modelcontextprotocol/servers
- Community: MCP Discord/Slack

## 📝 Next Steps

1. Configure your developer environment
2. Set up API tokens
3. Test each server individually
4. Start using with your AI agents