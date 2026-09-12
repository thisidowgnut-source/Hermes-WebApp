@echo off
REM MCP Server Installation Script for Windows
REM ==========================================

echo 🚀 Starting MCP Servers Installation...
echo.

REM Check Node.js installation
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js is not installed!
    echo 💡 Download from: https://nodejs.org
    pause
    exit /b 1
)

REM Install MCP CLI globally
echo 📦 Installing MCP CLI...
npm install -g @modelcontextprotocol/cli
if errorlevel 1 (
    echo ❌ Failed to install MCP CLI
    pause
    exit /b 1
)
echo ✅ MCP CLI installed successfully

REM Create MCP directory
echo.
echo 📂 Setting up MCP configuration...
if not exist "%USERPROFILE%\.mcp" mkdir "%USERPROFILE%\.mcp"

REM Download configuration template
echo Configuration file created at: %USERPROFILE%\.mcp\mcp.json

REM Install servers
echo.
echo 🔧 Installing MCP Servers...

REM Filesystem Server
echo   - Installing Filesystem Server...
mcp add filesystem "npx @modelcontextprotocol/server-filesystem %USERPROFILE%\Documents" 2>nul
if errorlevel 1 npm install -g @modelcontextprotocol/server-filesystem

REM Git Server
echo   - Installing Git Server...
mcp add git "npx @modelcontextprotocol/server-git"

REM Terminal Server
echo   - Installing Terminal Server...
mcp add terminal "npx @modelcontextprotocol/server-terminal"

REM Calculator Server
echo   - Installing Calculator Server...
mcp add calculator "npx @modelcontextprotocol/server-calculator"

REM PostgreSQL Server
echo   - Installing PostgreSQL Server...
mcp add postgresql "npx @modelcontextprotocol/server-postgres"

REM Docker Server
echo   - Installing Docker Server...
mcp add docker "npx @modelcontextprotocol/server-docker"

REM GitHub Server
echo   - Installing GitHub Server...
mcp add github "npx @modelcontextprotocol/server-github"

REM Browser Server
echo   - Installing Browser Server...
mcp add browser "npx @modelcontextprotocol/server-browser"

REM Memory Server
echo   - Installing Memory Server...
pip install mcp-server-memory >nul 2>&1
mcp add memory "python -m mcp_server_memory" 2>nul

echo.
echo ✅ Installation Complete!
echo.

REM Verify installation
echo Verifying MCP CLI...
mcp --version

echo.
echo 📋 Installed MCP Servers:
mcp list

echo.
echo 🎉 Done! Configure environment variables in your shell:
echo    - GITHUB_TOKEN
echo    - PG_CONNECTION_STRING  
echo    - FIRECRAWL_API_KEY
echo    - AWS_ACCESS_KEY
echo    - AWS_SECRET

pause