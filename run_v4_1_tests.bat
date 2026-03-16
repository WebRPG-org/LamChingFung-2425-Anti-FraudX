@echo off
REM AI 防詐平台 v4.1 - 測試運行腳本
REM 運行所有 v4.1 改進的單元測試

echo ========================================
echo AI 防詐平台 v4.1 - 單元測試
echo ========================================
echo.

REM 切換到 backend 目錄
cd /d "%~dp0backend"

echo [1/4] 檢查 Python 環境...
python --version
if %errorlevel% neq 0 (
    echo ❌ Python 未安裝或未加入 PATH
    pause
    exit /b 1
)
echo ✅ Python 環境正常
echo.

echo [2/4] 檢查 pytest...
python -m pytest --version
if %errorlevel% neq 0 (
    echo ⚠️ pytest 未安裝，正在安裝...
    pip install pytest pytest-asyncio
)
echo ✅ pytest 已安裝
echo.

echo [3/4] 運行 v4.1 改進測試...
echo.
python -m pytest tests/test_v4_1_improvements.py -v -s --tb=short

if %errorlevel% neq 0 (
    echo.
    echo ❌ 測試失敗！
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo ✅ 所有測試通過！
echo ========================================
echo.

echo [4/4] 生成測試報告...
python -m pytest tests/test_v4_1_improvements.py --html=test_report_v4.1.html --self-contained-html

if exist test_report_v4.1.html (
    echo ✅ 測試報告已生成: test_report_v4.1.html
    echo.
    echo 是否打開測試報告？(Y/N)
    set /p open_report=
    if /i "%open_report%"=="Y" (
        start test_report_v4.1.html
    )
) else (
    echo ⚠️ 測試報告生成失敗（可能需要安裝 pytest-html）
    echo 運行: pip install pytest-html
)

echo.
echo 測試完成！
pause

