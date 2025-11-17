@echo off
chcp 65001 >nul
echo ========================================
echo AI-Agent 快速啟動腳本 (Gemma 3 4B)
echo ========================================
echo.
echo 系統配置: Gemma 3 4B 基礎模型
echo Fine-Tuning: 自動訓練數據生成
echo.
echo ========================================
echo.

echo [1/4] 檢查 Python...
python --version
if errorlevel 1 (
    echo 錯誤：未找到 Python
    pause
    exit /b 1
)

echo.
echo [2/4] 安裝依賴...
cd backend
pip install -q fastapi uvicorn requests python-dotenv python-multipart
if errorlevel 1 (
    echo 警告：部分依賴安裝失敗，嘗試繼續...
)

echo.
echo [3/4] 檢查 .env 文件...
if not exist .env (
    echo 創建 .env 文件...
    (
        echo AGENT_MODEL=gemma3:4b
        echo OLLAMA_BASE_URL=http://127.0.0.1:11434
    ) > .env
    echo .env 文件已創建
) else (
    echo .env 文件已存在
)

echo.
echo [4/4] 檢查 Ollama...
curl -s http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo.
    echo ⚠️  警告：Ollama 似乎未運行
    echo.
    echo 請確保：
    echo 1. 已安裝 Ollama: https://ollama.com
    echo 2. 已下載模型: ollama pull gemma3:4b
    echo 3. Ollama 正在運行: ollama serve
    echo.
    pause
)

echo.
echo ========================================
echo 啟動 AI-Agent 系統...
echo ========================================
echo.
echo 系統將在 http://localhost:8000 啟動
echo 按 Ctrl+C 停止服務
echo.
echo 💡 提示:
echo    - 每次模擬結束後自動生成訓練數據
echo    - 訓練模型: python backend/scripts/run_finetuning.py --model both
echo    - 評估模型: python backend/scripts/evaluate_finetuned_models.py
echo    - 查看文檔: GEMMA3_配置說明.md
echo.

python main.py

pause


