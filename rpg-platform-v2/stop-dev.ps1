# Stop RPG Dev Server
# Clean all ports and processes

Write-Host ""
Write-Host "=== Stopping RPG Dev Server ===" -ForegroundColor Red
Write-Host ""

# Stop all Node processes
Write-Host "Stopping all Node processes..." -ForegroundColor Yellow
Get-Process -Name node -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue

# Clean ports 3000-3010
Write-Host "Cleaning ports..." -ForegroundColor Yellow
$ports = 3000..3010
foreach ($port in $ports) {
    $connections = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if ($connections) {
        foreach ($conn in $connections) {
            Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
        }
    }
}

# Double check with netstat
netstat -ano | findstr ":300" | ForEach-Object {
    $parts = $_ -split '\s+'
    $processId = $parts[-1]
    if ($processId -match '^\d+$') {
        Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
    }
}

Start-Sleep -Seconds 1

Write-Host ""
Write-Host "All servers stopped successfully" -ForegroundColor Green
Write-Host ""
