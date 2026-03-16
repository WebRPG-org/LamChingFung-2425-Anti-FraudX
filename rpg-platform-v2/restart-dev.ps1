# RPG Dev Server Manager
# Stop all ports and restart cleanly

Write-Host ""
Write-Host "=== RPG Dev Server Manager ===" -ForegroundColor Cyan
Write-Host ""

# 1. Stop all Node processes
Write-Host "Step 1: Stopping all Node processes..." -ForegroundColor Yellow
Get-Process -Name node -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 1

# 2. Clean ports 3000-3010
Write-Host "Step 2: Cleaning ports 3000-3010..." -ForegroundColor Yellow
$ports = 3000..3010
foreach ($port in $ports) {
    $connections = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if ($connections) {
        foreach ($conn in $connections) {
            try {
                Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
                Write-Host "  Cleaned port $port" -ForegroundColor Green
            } catch {
                # Ignore errors
            }
        }
    }
}

Start-Sleep -Seconds 2

# 3. Verify port 3000 is clear
Write-Host ""
Write-Host "Step 3: Verifying port status..." -ForegroundColor Yellow
$port3000 = Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue
if ($port3000) {
    Write-Host "  Port 3000 still in use, forcing cleanup..." -ForegroundColor Red
    netstat -ano | findstr :3000 | ForEach-Object {
        $parts = $_ -split '\s+'
        $processId = $parts[-1]
        if ($processId -match '^\d+$') {
            Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
        }
    }
    Start-Sleep -Seconds 1
} else {
    Write-Host "  Port 3000 is clear" -ForegroundColor Green
}

# 4. Start dev server
Write-Host ""
Write-Host "Step 4: Starting dev server..." -ForegroundColor Yellow
Set-Location "C:\Users\fungr\Documents\AI-Agentv4\rpg-platform-v2"

Write-Host ""
npm run dev
