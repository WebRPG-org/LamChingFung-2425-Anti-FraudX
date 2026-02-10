@echo off
REM 系統整合驗證腳本 (Windows批處理)

echo ========================================
echo 評分系統v2.0 整合驗證
echo ========================================
echo.

REM 設置Python路徑
set PYTHONPATH=%CD%

REM 運行驗證腳本
python scripts/validate_integration.py

REM 檢查退出碼
if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo 驗證成功！系統已準備好部署
    echo ========================================
) else (
    echo.
    echo ========================================
    echo 驗證失敗！請檢查錯誤信息
    echo ========================================
)

pause
