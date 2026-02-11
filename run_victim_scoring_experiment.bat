@echo off
REM 受害人Agent評分實驗運行腳本

echo ========================================
echo 受害人Agent評分實驗
echo ========================================
echo.

cd /d "%~dp0"

echo [1/3] 檢查Python環境...
py --version
if %errorlevel% neq 0 (
    echo 錯誤: Python未安裝或不在PATH中
    pause
    exit /b 1
)
echo.

echo [2/3] 檢查依賴...
py -c "import google.adk" 2>nul
if %errorlevel% neq 0 (
    echo 警告: google.adk未安裝，某些功能可能無法使用
)
echo.

echo [3/3] 運行實驗...
echo.
py backend/experiments/test_victim_scoring.py

echo.
echo ========================================
echo 實驗完成
echo ========================================
pause
