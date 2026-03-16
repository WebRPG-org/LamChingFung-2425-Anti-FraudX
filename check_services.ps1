# AI-Agentv4 服務狀態檢查腳本 (PowerShell)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  AI-Agentv4 服務狀態" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 檢查 Backend
Write-Host "[Backend 服務狀態]" -ForegroundColor Yellow
Write-Host ""

$backendProcesses = Get-Process -Name python -ErrorAction SilentlyContinue | Where-Object { 
    $_.MainWindowTitle -like "*Backend*" -or $_.CommandLine -like "*main.py*"
}

if ($backendProcesses) {
    Write-Host "✅ Backend 正在運行" -ForegroundColor Green
    Write-Host ""
    Write-Host "進程詳情：" -ForegroundColor White
    $backendProcesses | ForEach-Object {
        Write-Host "  PID: $($_.Id)" -ForegroundColor Cyan
        Write-Host "  CPU: $($_.CPU.ToString('0.00'))%" -ForegroundColor Cyan
        Write-Host "  Memory: $([math]::Round($_.WorkingSet64 / 1MB, 2)) MB" -ForegroundColor Cyan
        Write-Host "  Start Time: $($_.StartTime)" -ForegroundColor Cyan
    }
} else {
    Write-Host "❌ Backend 未運行" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 檢查 Vite
Write-Host "[Vite 服務狀態]" -ForegroundColor Yellow
Write-Host ""

$viteProcesses = Get-Process -Name node -ErrorAction SilentlyContinue | Where-Object { 
    $_.MainWindowTitle -like "*Vite*" -or $_.CommandLine -like "*vite*"
}

if ($viteProcesses) {
    Write-Host "✅ Vite 正在運行" -ForegroundColor Green
    Write-Host ""
    Write-Host "進程詳情：" -ForegroundColor White
    $viteProcesses | ForEach-Object {
        Write-Host "  PID: $($_.Id)" -ForegroundColor Cyan
        Write-Host "  CPU: $($_.CPU.ToString('0.00'))%" -ForegroundColor Cyan
        Write-Host "  Memory: $([math]::Round($_.WorkingSet64 / 1MB, 2)) MB" -ForegroundColor Cyan
        Write-Host "  Start Time: $($_.StartTime)" -ForegroundColor Cyan
    }
} else {
    Write-Host "❌ Vite 未運行" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 檢查端口
Write-Host "[端口佔用情況]" -ForegroundColor Yellow
Write-Host ""

Write-Host "Backend (8000):" -ForegroundColor White
$port8000 = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
if ($port8000) {
    Write-Host "  ✅ 端口已佔用 (PID: $($port8000.OwningProcess))" -ForegroundColor Green
} else {
    Write-Host "  ❌ 端口未佔用" -ForegroundColor Red
}

Write-Host ""
Write-Host "Vite (3000):" -ForegroundColor White
$port3000 = Get-NetTCPConnection -LocalPort 3000 -State Listen -ErrorAction SilentlyContinue
if ($port3000) {
    Write-Host "  ✅ 端口已佔用 (PID: $($port3000.OwningProcess))" -ForegroundColor Green
} else {
    Write-Host "  ❌ 端口未佔用" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 服務可訪問性測試
Write-Host "[服務可訪問性測試]" -ForegroundColor Yellow
Write-Host ""

Write-Host "測試 Backend API..." -ForegroundColor White
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/docs" -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop
    Write-Host "  ✅ Backend API 可訪問 (狀態碼: $($response.StatusCode))" -ForegroundColor Green
} catch {
    Write-Host "  ❌ Backend API 無法訪問" -ForegroundColor Red
}

Write-Host ""
Write-Host "測試 Vite 前端..." -ForegroundColor White
try {
    $response = Invoke-WebRequest -Uri "http://localhost:3000" -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop
    Write-Host "  ✅ Vite 前端可訪問 (狀態碼: $($response.StatusCode))" -ForegroundColor Green
} catch {
    Write-Host "  ❌ Vite 前端無法訪問" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "按任意鍵退出..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
