@echo off
setlocal enabledelayedexpansion
chcp 65001 > nul

SET SCRIPT_DIR=%~dp0
CD /d "%SCRIPT_DIR%"

echo.
echo ================================================================================
echo AI反詐騙平台 - 本地開發模式啟動 (Gemma 3 4B Edition)
echo ================================================================================
echo.
echo 系統配置: 使用 Gemma 3 4B 作為基礎模型
echo Fine-Tuning 支持: 自動生成訓練數據
echo.
echo ================================================================================
echo.

echo [步骤1/4] 清理旧的进程...
taskkill /F /IM "ollama.exe" /T >nul 2>&1
taskkill /F /IM "ollama app.exe" /T >nul 2>&1
taskkill /F /IM "python.exe" /FI "WINDOWTITLE eq *start_server*" /T >nul 2>&1
timeout /t 2 /nobreak >nul
echo [OK] 清理完成
echo.

echo [步骤2/4] 启动Ollama服务 (监听所有接口)...
set OLLAMA_HOST=0.0.0.0:11434
start /B ollama serve
echo    等待Ollama启动 (8秒)...
timeout /t 8 /nobreak >nul

curl -s http://localhost:11434/api/tags >nul 2>&1
if %errorlevel% neq 0 (
    echo [X] Ollama启动失败
    echo    请手动运行: ollama serve
    pause
    exit /b 1
)
echo [OK] Ollama服务运行在 0.0.0.0:11434
echo.

echo [步骤3/4] 檢查 Gemma 3 4B 模型...
ollama list | findstr "gemma3:4b" >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Gemma 3 4B 未安裝，自動下載中...
    echo     這是 Fine-Tuning 的默認基礎模型
    echo     需要 3.3GB 空間，預計 5-10 分鐘
    echo.
    ollama pull gemma3:4b
    if !errorlevel! equ 0 (
        echo [OK] Gemma 3 4B 下載完成
    ) else (
        echo [!] 下載失敗，請稍後手動下載: ollama pull gemma3:4b
        echo     系統將使用已安裝的其他模型
    )
) else (
    echo [OK] Gemma 3 4B 已就緒
)
echo.

echo [步驟3.5/4] 檢查GPU狀態...
nvidia-smi --query-gpu=name,utilization.gpu --format=csv,noheader 2>nul
if %errorlevel% neq 0 (
    echo [!] 無法獲取GPU信息 (使用CPU模式)
) else (
    echo [OK] GPU可用 (本地模式使用CPU以簡化配置)
)
echo.

echo [步骤4/4] 啟動Python後端服務...
echo    服務地址: http://localhost:8000
echo    前端地址: http://localhost:8000 (打開瀏覽器訪問)
echo    按 Ctrl+C 停止服務
echo.
echo ================================================================================
echo [OK] 啟動完成！
echo ================================================================================
echo.
echo 💡 快速提示:
echo    - 模擬結束後會自動生成 Fine-Tuning 訓練數據
echo    - 訓練數據保存在: backend/training_data/finetuning/
echo    - 使用 Gemma 3 4B 訓練: python backend/scripts/run_finetuning.py --model both
echo    - 查看文檔: GEMMA3_配置說明.md
echo.
echo ================================================================================
echo.

REM 启动Python服务器
python start_server.py

REM 如果服务器停止，清理
echo.
echo 正在清理...
taskkill /F /IM "ollama.exe" /T >nul 2>&1
echo 服务已停止
pause

