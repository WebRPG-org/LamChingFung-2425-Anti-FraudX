# Phase 2 測試運行腳本 (PowerShell)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Phase 2: 自適應權重優化器測試" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Set-Location $PSScriptRoot

Write-Host "[1/3] 檢查Python環境..." -ForegroundColor Yellow
try {
    $pythonVersion = py --version 2>&1
    Write-Host "✓ $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Python未安裝或不在PATH中" -ForegroundColor Red
    Read-Host "按Enter鍵退出"
    exit 1
}
Write-Host ""

Write-Host "[2/3] 檢查pytest..." -ForegroundColor Yellow
try {
    $pytestVersion = py -m pytest --version 2>&1
    Write-Host "✓ pytest已安裝" -ForegroundColor Green
} catch {
    Write-Host "安裝pytest..." -ForegroundColor Yellow
    py -m pip install pytest
}
Write-Host ""

Write-Host "[3/3] 運行測試套件..." -ForegroundColor Yellow
Write-Host ""
py -m pytest backend/tests/test_adaptive_scoring.py -v --tb=short

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "測試完成" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Read-Host "按Enter鍵退出"
