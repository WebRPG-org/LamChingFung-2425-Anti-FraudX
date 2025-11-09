@echo off
chcp 65001 > nul

SET SCRIPT_DIR=%~dp0
CD /d "%SCRIPT_DIR%"

echo.
echo ================================================================================
echo AI反诈骗平台 - 一键启动 (GPU加速)
echo ================================================================================
echo.

echo [步骤1/5] 清理旧的Ollama进程...
taskkill /F /IM "ollama.exe" /T >nul 2>&1
taskkill /F /IM "ollama app.exe" /T >nul 2>&1
timeout /t 2 /nobreak >nul
echo [OK] 清理完成
echo.

echo [步骤2/5] 启动Ollama服务 (监听所有接口)...
set OLLAMA_HOST=0.0.0.0:11434
start /B ollama serve
echo    等待Ollama启动 (10秒)...
timeout /t 10 /nobreak >nul

curl -s http://localhost:11434/api/tags >nul 2>&1
if %errorlevel% neq 0 (
    echo [X] Ollama启动失败
    echo    请手动运行: ollama serve
    pause
    exit /b 1
)
echo [OK] Ollama服务运行在 0.0.0.0:11434
echo.

echo [步骤3/5] 检查GPU使用...
nvidia-smi --query-gpu=name,utilization.gpu --format=csv,noheader 2>nul
if %errorlevel% neq 0 (
    echo [!] 无法获取GPU信息
)
echo.

echo [步骤4/5] 启动Docker Backend...
docker-compose -f docker-compose.local.yml down >nul 2>&1
docker-compose -f docker-compose.local.yml up -d
if %errorlevel% neq 0 (
    echo [X] Backend启动失败
    pause
    exit /b 1
)
echo [OK] Backend容器已启动
echo.

echo [步骤5/5] 等待服务就绪 (15秒)...
timeout /t 15 /nobreak >nul
echo.

echo 验证服务...
docker ps --filter "name=ai-antiscam-backend" --format "{{.Names}}: {{.Status}}"
echo.
netstat -ano | findstr ":11434" | findstr "LISTENING" >nul 2>&1
if %errorlevel% equ 0 (echo [OK] Ollama: http://localhost:11434)
netstat -ano | findstr ":8000" | findstr "LISTENING" >nul 2>&1
if %errorlevel% equ 0 (echo [OK] Backend: http://localhost:8000)
echo.

echo ================================================================================
echo [OK] 部署完成！
echo ================================================================================
echo.
echo 访问服务:
echo   Web界面: http://localhost:8000
echo   API文档: http://localhost:8000/docs
echo.
echo 监控GPU (在新窗口):
echo   nvidia-smi -l 1
echo.
echo 查看日志:
echo   docker logs -f ai-antiscam-backend
echo.
echo 停止服务:
echo   docker-compose -f docker-compose.local.yml down
echo   taskkill /F /IM ollama.exe
echo.
pause

