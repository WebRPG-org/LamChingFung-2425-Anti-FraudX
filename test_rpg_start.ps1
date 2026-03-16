# RPGv2 啟動腳本 (PowerShell)
$ErrorActionPreference = "Stop"

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "RPGv2 服務啟動測試" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

# 切換到項目根目錄
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

Write-Host "[1] 檢查 RPGv2 目錄..." -ForegroundColor Yellow
if (Test-Path "rpg-platform-v2") {
    Write-Host "✅ RPGv2 目錄存在" -ForegroundColor Green
} else {
    Write-Host "❌ RPGv2 目錄不存在" -ForegroundColor Red
    exit 1
}
Write-Host ""

Write-Host "[2] 檢查 package.json..." -ForegroundColor Yellow
if (Test-Path "rpg-platform-v2\package.json") {
    Write-Host "✅ package.json 存在" -ForegroundColor Green
} else {
    Write-Host "❌ package.json 不存在" -ForegroundColor Red
    exit 1
}
Write-Host ""

Write-Host "[3] 檢查 node_modules..." -ForegroundColor Yellow
if (Test-Path "rpg-platform-v2\node_modules") {
    Write-Host "✅ node_modules 存在" -ForegroundColor Green
} else {
    Write-Host "⚠️  node_modules 不存在，正在安裝..." -ForegroundColor Yellow
    Set-Location "rpg-platform-v2"
    npm install
    Set-Location ".."
}
Write-Host ""

Write-Host "[4] 啟動 RPGv2 服務（背景模式）..." -ForegroundColor Yellow
Set-Location "rpg-platform-v2"

# 使用 Start-Process 在新窗口中啟動
$process = Start-Process -FilePath "npm" -ArgumentList "run", "dev" -PassThru -WindowStyle Minimized
Write-Host "✅ RPGv2 已啟動 (PID: $($process.Id))" -ForegroundColor Green
Set-Location ".."
Write-Host ""

Write-Host "[5] 等待服務啟動..." -ForegroundColor Yellow
Start-Sleep -Seconds 5
Write-Host ""

Write-Host "[6] 測試服務可訪問性..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:3000" -TimeoutSec 3 -UseBasicParsing -ErrorAction Stop
    Write-Host "✅ RPGv2 可訪問 (狀態碼: $($response.StatusCode))" -ForegroundColor Green
} catch {
    Write-Host "⚠️  RPGv2 可能還在啟動中..." -ForegroundColor Yellow
    Write-Host "   錯誤: $($_.Exception.Message)" -ForegroundColor Gray
}
Write-Host ""

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "📍 服務地址: http://localhost:3000" -ForegroundColor White
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "按任意鍵退出..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
