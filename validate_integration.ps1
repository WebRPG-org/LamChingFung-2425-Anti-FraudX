# 系統整合驗證腳本 (PowerShell)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "評分系統v2.0 整合驗證" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 設置Python路徑
$env:PYTHONPATH = $PWD

# 運行驗證腳本
python scripts/validate_integration.py

# 檢查退出碼
if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "驗證成功！系統已準備好部署" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "驗證失敗！請檢查錯誤信息" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
}

Read-Host -Prompt "按Enter鍵退出"
