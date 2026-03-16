# AI-Agentv4 服務停止腳本 (PowerShell)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  停止 AI-Agentv4 服務" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 停止 Backend
Write-Host "[1/2] 停止 Backend 服務..." -ForegroundColor Yellow

$backendProcesses = Get-Process -Name python -ErrorAction SilentlyContinue | Where-Object { 
    $_.MainWindowTitle -like "*Backend*" -or $_.CommandLine -like "*main.py*"
}

if ($backendProcesses) {
    $backendProcesses | ForEach-Object {
        Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
        Write-Host "✅ 已停止 Backend (PID: $($_.Id))" -ForegroundColor Green
    }
} else {
    Write-Host "⚠️  Backend 未運行或已停止" -ForegroundColor Yellow
}

Write-Host ""

# 停止 Vite
Write-Host "[2/2] 停止 Vite 服務..." -ForegroundColor Yellow

$viteProcesses = Get-Process -Name node -ErrorAction SilentlyContinue | Where-Object { 
    $_.MainWindowTitle -like "*Vite*" -or $_.CommandLine -like "*vite*"
}

if ($viteProcesses) {
    $viteProcesses | ForEach-Object {
        Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
        Write-Host "✅ 已停止 Vite (PID: $($_.Id))" -ForegroundColor Green
    }
} else {
    Write-Host "⚠️  Vite 未運行或已停止" -ForegroundColor Yellow
}

Write-Host ""

# 額外清理：檢查端口佔用
Write-Host "[額外] 檢查端口佔用..." -ForegroundColor Yellow

$port8000 = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
if ($port8000) {
    $pid = $port8000.OwningProcess
    Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
    Write-Host "✅ 已釋放端口 8000 (PID: $pid)" -ForegroundColor Green
}

$port3000 = Get-NetTCPConnection -LocalPort 3000 -State Listen -ErrorAction SilentlyContinue
if ($port3000) {
    $pid = $port3000.OwningProcess
    Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
    Write-Host "✅ 已釋放端口 3000 (PID: $pid)" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  🎉 所有服務已停止！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "按任意鍵退出..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
