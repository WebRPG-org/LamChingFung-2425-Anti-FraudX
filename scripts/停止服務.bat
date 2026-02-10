@echo off
chcp 65001 > nul

REM Get script directory and move to project root (parent dir)
SET SCRIPT_DIR=%~dp0
CD /d "%SCRIPT_DIR%.."

echo.
echo ================================================================================
echo 停止 AI反诈骗平台服务
echo ================================================================================
echo.

echo 正在停止 Python 服务器...
taskkill /F /IM "uvicorn.exe" /T >nul 2>&1
taskkill /F /IM "python.exe" /T >nul 2>&1
echo [OK] 清理进程完成
echo.

echo 正在停止 Ollama 服务...
taskkill /F /IM "ollama.exe" /T >nul 2>&1
taskkill /F /IM "ollama app.exe" /T >nul 2>&1
echo [OK] Ollama服务已停止
echo.

echo 正在停止 Docker 容器 (如果有)...
docker-compose -f docker-compose.local.yml down >nul 2>&1
echo [OK] Docker清理完成
echo.

echo ================================================================================
echo [OK] 所有服务已停止
echo ================================================================================
echo.
pause
