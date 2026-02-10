@echo off
REM Phase 2 測試運行腳本

echo ========================================
echo Phase 2: 自適應權重優化器測試
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

echo [2/3] 檢查pytest...
py -m pytest --version
if %errorlevel% neq 0 (
    echo 安裝pytest...
    py -m pip install pytest
)
echo.

echo [3/3] 運行測試套件...
echo.
py -m pytest backend/tests/test_adaptive_scoring.py -v --tb=short

echo.
echo ========================================
echo 測試完成
echo ========================================
pause
