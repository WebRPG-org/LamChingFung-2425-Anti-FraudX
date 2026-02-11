# AI-Agentv4 服務啟動腳本 (PowerShell)
# 背景運行 Backend 和 Vite 服務

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  AI-Agentv4 服務啟動腳本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 獲取腳本目錄
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path

# 檢查現有服務
Write-Host "[1/3] 檢查現有服務..." -ForegroundColor Yellow

$backendRunning = Get-Process -Name python -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowTitle -like "*Backend*" }
if ($backendRunning) {
    Write-Host "⚠️  Backend 已在運行 (PID: $($backendRunning.Id))" -ForegroundColor Yellow
} else {
    Write-Host "✅ Backend 未運行" -ForegroundColor Green
}

$viteRunning = Get-Process -Name node -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowTitle -like "*Vite*" }
if ($viteRunning) {
    Write-Host "⚠️  Vite 已在運行 (PID: $($viteRunning.Id))" -ForegroundColor Yellow
} else {
    Write-Host "✅ Vite 未運行" -ForegroundColor Green
}

Write-Host ""

# 啟動 Backend
Write-Host "[2/3] 啟動 Backend 服務（背景運行）..." -ForegroundColor Yellow

$backendPath = Join-Path $scriptPath "backend"
$backendCmd = "cd '$backendPath'; py main.py"

Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCmd -WindowStyle Minimized

Start-Sleep -Seconds 3
Write-Host "✅ Backend 已啟動（端口 8000）" -ForegroundColor Green

Write-Host ""

# 啟動 Vite
Write-Host "[3/3] 啟動 Vite 前端服務（背景運行）..." -ForegroundColor Yellow

$viteCmd = "cd '$scriptPath'; npm run dev"

Start-Process powershell -ArgumentList "-NoExit", "-Command", $viteCmd -WindowStyle Minimized

Start-Sleep -Seconds 3
Write-Host "✅ Vite 已啟動（端口 5173）" -ForegroundColor Green

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  🎉 所有服務已啟動！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "📍 服務地址：" -ForegroundColor White
Write-Host "   - Frontend: " -NoNewline -ForegroundColor White
Write-Host "http://localhost:3000" -ForegroundColor Cyan
Write-Host "   - Backend:  " -NoNewline -ForegroundColor White
Write-Host "http://localhost:8000" -ForegroundColor Cyan
Write-Host "   - API Docs: " -NoNewline -ForegroundColor White
Write-Host "http://localhost:8000/docs" -ForegroundColor Cyan

Write-Host ""
Write-Host "💡 提示：" -ForegroundColor White
Write-Host "   - 服務在背景運行，關閉此窗口不影響服務" -ForegroundColor Gray
Write-Host "   - 使用 " -NoNewline -ForegroundColor Gray
Write-Host ".\stop_services.ps1" -NoNewline -ForegroundColor Yellow
Write-Host " 停止所有服務" -ForegroundColor Gray
Write-Host "   - 使用 " -NoNewline -ForegroundColor Gray
Write-Host ".\check_services.ps1" -NoNewline -ForegroundColor Yellow
Write-Host " 查看服務狀態" -ForegroundColor Gray

Write-Host ""
Write-Host "按任意鍵退出..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
