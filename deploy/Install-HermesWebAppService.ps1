<#
.SYNOPSIS
    Install Hermes WebApp as a Windows Service using NSSM
.DESCRIPTION
    Creates a Windows Service that auto-starts Hermes WebApp on boot,
    restarts on crash, and runs in the background.
.NOTES
    Requires: NSSM (Non-Sucking Service Manager) - https://nssm.cc/download
    Run as Administrator
#>

param(
    [string]$InstallPath = "C:\Users\megat\Hermes-WebApp",
    [string]$ServiceName = "HermesWebApp",
    [string]$DisplayName = "Hermes OS WebApp",
    [string]$Description = "Telegram Mini App Backend for Remote PC Control",
    [string]$PythonPath = "C:\Users\megat\AppData\Local\Programs\Python\Python311\python.exe",
    [switch]$StartService = $true
)

# Check for NSSM
$nssmPath = "C:\nssm\nssm.exe"
if (-not (Test-Path $nssmPath)) {
    Write-Warning "NSSM not found at $nssmPath"
    Write-Host "Download from: https://nssm.cc/download"
    Write-Host "Extract to C:\nssm\"
    exit 1
}

# Check Python
if (-not (Test-Path $PythonPath)) {
    Write-Warning "Python not found at $PythonPath"
    Write-Host "Update \$PythonPath parameter to your Python executable"
    exit 1
}

# Check project directory
if (-not (Test-Path $InstallPath)) {
    Write-Error "Install path not found: $InstallPath"
    exit 1
}

Write-Host "Installing Hermes WebApp as Windows Service..." -ForegroundColor Cyan

# Stop existing service if running
if (Get-Service $ServiceName -ErrorAction SilentlyContinue) {
    Write-Host "Stopping existing service..." -ForegroundColor Yellow
    nssm stop $ServiceName
    nssm remove $ServiceName confirm
}

# Install service
Write-Host "Creating service..." -ForegroundColor Green
& $nssmPath install $ServiceName $PythonPath "-m uvicorn backend.main:app --host 127.0.0.1 --port 9220"
& $nssmPath set $ServiceName AppDirectory $InstallPath
& $nssmPath set $ServiceName AppStdout "$InstallPath\logs\hermes-webapp-out.log"
& $nssmPath set $ServiceName AppStderr "$InstallPath\logs\hermes-webapp-err.log"
& $nssmPath set $ServiceName AppEnvironmentExtra "PYTHONPATH=$InstallPath"
& $nssmPath set $ServiceName AppEnvironmentExtra "HERMES_ENV=production"
& $nssmPath set $ServiceName Start SERVICE_AUTO_START
& $nssmPath set $ServiceName Description $Description
& $nssmPath set $ServiceName DisplayName $DisplayName
& $nssmPath set $ServiceName AppExit Default Restart
& $nssmPath set $ServiceName AppThrottle 5000
& $nssmPath set $ServiceName AppRestartDelay 5000

# Set environment variables from .env file
$envFile = Join-Path $InstallPath ".env"
if (Test-Path $envFile) {
    Write-Host "Loading environment from .env..." -ForegroundColor Green
    Get-Content $envFile | Where-Object { $_ -match "^[A-Z_]+=" } | ForEach-Object {
        if ($_ -match "^([A-Z_]+)=(.*)$") {
            $key = $matches[1]
            $value = $matches[2].Trim('"')
            & $nssmPath set $ServiceName AppEnvironmentExtra "$key=$value"
            Write-Host "  Set $key" -ForegroundColor Gray
        }
    }
}

# Ensure logs directory exists
New-Item -ItemType Directory -Force -Path "$InstallPath\logs" | Out-Null

if ($StartService) {
    Write-Host "Starting service..." -ForegroundColor Green
    & $nssmPath start $ServiceName
    Start-Sleep 3
    $status = & $nssmPath status $ServiceName
    Write-Host "Service status: $status" -ForegroundColor Cyan
}

Write-Host "`nService installed successfully!" -ForegroundColor Green
Write-Host "Manage with: nssm start|stop|restart|status $ServiceName" -ForegroundColor Cyan
Write-Host "View logs: Get-Content $InstallPath\logs\hermes-webapp-out.log -Wait" -ForegroundColor Cyan