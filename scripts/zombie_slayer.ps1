# Hermes Zombie Slayer - Auto Memory Recovery
# Membunuh proses zombi (idle > 2 jam) tanpa mematikan proses aktif
$currentPid = $PID
$threshold = (Get-Date).AddHours(-2)

# Kill orphan node, python, webview2
Get-Process -Name "node", "msedgewebview2", "python", "pythonw" -ErrorAction SilentlyContinue | 
    Where-Object { $_.StartTime -lt $threshold } | 
    Stop-Process -Force -ErrorAction SilentlyContinue

# Kill orphan pwsh, leaving current script alone
Get-Process -Name "pwsh" -ErrorAction SilentlyContinue | 
    Where-Object { $_.Id -ne $currentPid -and $_.StartTime -lt $threshold } | 
    Stop-Process -Force -ErrorAction SilentlyContinue
