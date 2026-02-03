@echo off
chcp 65001 >nul
echo ========================================
echo   AI 反詐騙模擬訓練平台 - 快速啟動
echo ========================================
echo.

REM 設置環境變量（禁用強制 GPU 模式）
set FORCE_GPU=0
set OLLAMA_BASE_URL=http://localhost:11434

echo [✓] 環境變量已設置
echo     FORCE_GPU=0 (允許使用 CPU)
echo     OLLAMA_BASE_URL=%OLLAMA_BASE_URL%
echo.

REM 切換到項目根目錄
cd /d "%~dp0\.."

echo [✓] 當前目錄: %CD%
echo.

REM 啟動服務器
echo [→] 正在啟動服務器...
echo     服務器地址: http://localhost:8000
echo     API 文檔: http://localhost:8000/docs
echo     測試端點: http://localhost:8000/test
echo.
echo [!] 按 Ctrl+C 停止服務器
echo ========================================
echo.

python scripts\start_server.py

pause
