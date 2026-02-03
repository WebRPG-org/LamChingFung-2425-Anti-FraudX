@echo off
chcp 65001 > nul

REM Get script directory and move to project root (parent dir)
SET SCRIPT_DIR=%~dp0
CD /d "%SCRIPT_DIR%.."

echo.
echo ================================================================================
echo AI反诈骗平台 - 一键启动 (调试模式)
echo ================================================================================
echo 工作目录: %CD%
echo.

echo [步骤1/4] 清理旧的进程...
taskkill /F /IM "uvicorn.exe" /T >nul 2>&1
taskkill /F /IM "python.exe" /T >nul 2>&1
timeout /t 1 /nobreak >nul
echo [OK] 清理完成
echo.

echo [步骤2/4] 检查 Ollama 服务...
curl -s http://localhost:11434/api/tags >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Ollama 未运行，正在尝试启动...
    start /B ollama serve
    echo    等待Ollama启动 10秒...
    timeout /t 10 /nobreak >nul
    
    curl -s http://localhost:11434/api/tags >nul 2>&1
    if %errorlevel% neq 0 (
        echo [X] Ollama启动失败
        echo    请手动运行: ollama serve
        pause
        exit /b 1
    )
)
echo [OK] Ollama服务运行在 http://localhost:11434
echo.

echo [步骤3/4] 启动 Python Backend...
if not exist "backend\.env" (
    echo [!] 警告: backend\.env 不存在，将尝试使用默认设置
)

echo ================================================================================
echo 正在启动服务器... 请勿关闭此窗口
echo ================================================================================
echo.

REM 直接在当前窗口运行，不使用 start
python scripts\start_server.py

pause
