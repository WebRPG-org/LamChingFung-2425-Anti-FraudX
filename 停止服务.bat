@echo off
chcp 65001 > nul

echo.
echo ================================================================================
echo 停止 AI反诈骗平台服务
echo ================================================================================
echo.

echo 正在停止 Python 服务器...
taskkill /F /IM "python.exe" /FI "WINDOWTITLE eq *start_server*" /T >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Python服务器已停止
) else (
    echo [!] 没有运行中的Python服务器
)
echo.

echo 正在停止 Ollama 服务...
taskkill /F /IM "ollama.exe" /T >nul 2>&1
taskkill /F /IM "ollama app.exe" /T >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Ollama服务已停止
) else (
    echo [!] 没有运行中的Ollama服务
)
echo.

echo 正在停止 Docker 容器 (如果有)...
docker-compose -f docker-compose.local.yml down >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Docker容器已停止
) else (
    echo [!] 没有运行中的Docker容器
)
echo.

echo ================================================================================
echo [OK] 所有服务已停止
echo ================================================================================
echo.
pause

