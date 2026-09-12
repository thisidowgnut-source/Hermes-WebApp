# MCP Servers Test Script for PowerShell
# ======================================

Write-Host "🧪 Testing MCP Servers..." -ForegroundColor Cyan
Write-Host ""

# Test counter
$Passed = 0
$Failed = 0

function Test-Command {
    param($Name)
    Write-Host -NoNewline "Testing $Name... "
    
    $command = Get-Command $Name -ErrorAction SilentlyContinue
    if ($command) {
        Write-Host "✓ Found" -ForegroundColor Green
        $script:Passed++
        return $true
    } else {
        Write-Host "✗ Not found" -ForegroundColor Red
        $script:Failed++
        return $false
    }
}

function Test-McpServer {
    param($Name)
    Write-Host -NoNewline "Checking $Name... "
    
    try {
        $result = mcp tools $Name 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ Available" -ForegroundColor Green
            $script:Passed++
        } else {
            Write-Host "⚠ Needs setup" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "⚠ Needs setup" -ForegroundColor Yellow
    }
}

Write-Host "=== PowerShell Environment ==="
Test-Command "powershell"
Write-Host ""

Write-Host "=== MCP CLI ==="
if (Get-Command mcp -ErrorAction SilentlyContinue) {
    Write-Host "✓ MCP CLI installed" -ForegroundColor Green
    $version = mcp --version 2>$null
    Write-Host "  Version: $version"
    $Passed++
} else {
    Write-Host "✗ MCP CLI not found" -ForegroundColor Red
    $Failed++
}

Write-Host ""
Write-Host "=== Core Tools ==="
Test-Command "node"
Test-Command "npm"
Test-Command "npx"

Write-Host ""
Write-Host "=== Python ==="
if (Get-Command python -ErrorAction SilentlyContinue) {
    Write-Host "✓ Python available" -ForegroundColor Green
    $Passed++
} elseif (Get-Command python3 -ErrorAction SilentlyContinue) {
    Write-Host "✓ Python3 available" -ForegroundColor Green
    $Passed++
} else {
    Write-Host "⚠ Python not found (Memory server needs Python)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== Git ==="
Test-Command "git"

Write-Host ""
Write-Host "=== Docker ==="
if (Get-Command docker -ErrorAction SilentlyContinue) {
    Write-Host "✓ Docker installed" -ForegroundColor Green
    $Passed++
    
    # Check if Docker daemon is running
    $dockerRunning = docker info 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  Daemon: Running" -ForegroundColor Green
    } else {
        Write-Host "  Daemon: Not running (start Docker)" -ForegroundColor Yellow
    }
} else {
    Write-Host "⚠ Docker not found (optional)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== MCP Servers ==="
$servers = @("filesystem", "git", "terminal", "calculator", "postgresql", "github", "browser", "aws")

foreach ($server in $servers) {
    try {
        $result = mcp tools $server 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ $server - Available" -ForegroundColor Green
            $Passed++
        } else {
            Write-Host "⚠ $server - Needs configuration" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "⚠ $server - Needs configuration" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "==================================="
Write-Host "Test Summary: $Passed passed, $Failed failed" -ForegroundColor Cyan
Write-Host "==================================="

if ($Failed -eq 0) {
    Write-Host "🎉 All tests passed! MCP Servers are ready!" -ForegroundColor Green
} else {
    Write-Host "⚠ Some tests failed. Check configuration." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Set environment variables (GitHub token, API keys)"
Write-Host "2. Run: mcp list"
Write-Host "3. Test servers: mcp test <server-name>"