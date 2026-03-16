# 受害人Agent評分實驗 (PowerShell版本)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "受害人Agent評分實驗" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 切換到腳本目錄
Set-Location $PSScriptRoot

# 檢查Python
Write-Host "檢查Python環境..." -ForegroundColor Yellow
$pythonVersion = py --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "錯誤: 找不到Python" -ForegroundColor Red
    Read-Host "按Enter鍵退出"
    exit 1
}
Write-Host "Python版本: $pythonVersion" -ForegroundColor Green
Write-Host ""

# 運行實驗
Write-Host "開始實驗..." -ForegroundColor Yellow
Write-Host ""

py scripts/run_victim_eval_experiment.py

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "實驗完成" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "結果已保存至 data/ 目錄" -ForegroundColor Green
Write-Host ""

Read-Host "按Enter鍵退出"
