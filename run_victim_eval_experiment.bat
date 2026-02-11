@echo off
echo ========================================
echo 受害人Agent評分實驗
echo ========================================
echo.

cd /d "%~dp0"

echo 檢查Python環境...
py --version
if errorlevel 1 (
    echo 錯誤: 找不到Python
    pause
    exit /b 1
)

echo.
echo 開始實驗...
echo.

py scripts/run_victim_eval_experiment.py

echo.
echo ========================================
echo 實驗完成
echo ========================================
echo.
echo 結果已保存至 data/ 目錄
echo.

pause
