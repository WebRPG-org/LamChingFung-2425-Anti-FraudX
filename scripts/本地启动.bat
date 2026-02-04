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

echo [步骤1/6] 清理旧的进程...
taskkill /F /IM "uvicorn.exe" /T >nul 2>&1
taskkill /F /IM "python.exe" /T >nul 2>&1
taskkill /F /IM "node.exe" /T >nul 2>&1
timeout /t 1 /nobreak >nul
echo [OK] 清理完成
echo.

echo [步骤2/6] 检查 Python 环境...
REM 嘗試使用 py 命令（Windows Python Launcher）
where py >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_CMD=py
    for /f "tokens=*" %%i in ('py --version') do set PYTHON_VERSION=%%i
    echo [OK] %PYTHON_VERSION% ^(使用 py 命令^)
) else (
    python --version >nul 2>&1
    if errorlevel 1 (
        echo [X] 错误: 未找到 Python，请先安装 Python 3.10+
        echo.
        echo 请前往 https://www.python.org/downloads/ 下载安装
        echo 安装时务必勾选 "Add Python to PATH"
        pause
        exit /b 1
    )
    set PYTHON_CMD=python
    for /f "tokens=*" %%i in ('python --version') do set PYTHON_VERSION=%%i
    echo [OK] %PYTHON_VERSION%
)
echo.

echo [步骤3/6] 检查 Node.js 环境...
node --version >nul 2>&1
if errorlevel 1 (
    echo [X] 错误: 未找到 Node.js，请先安装 Node.js 18+
    echo.
    echo 请前往 https://nodejs.org/ 下载安装
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('node --version') do set NODE_VERSION=%%i
echo [OK] Node.js %NODE_VERSION%
echo.

echo [步骤4/6] 检查 Ollama 服务...
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

echo [步骤5/6] 检查 RPGv2 依赖...
cd rpg-platform-v2
if not exist "node_modules" (
    echo [+] 安装 RPGv2 依赖（首次运行可能需要几分钟）...
    call npm install
    if errorlevel 1 (
        echo [X] RPGv2 依赖安装失败
        cd ..
        pause
        exit /b 1
    )
)
echo [OK] RPGv2 依赖已就绪
cd ..
echo.

echo [步骤6/6] 启动服务...
if not exist "backend\.env" (
    echo [!] 警告: backend\.env 不存在，将尝试使用默认设置
)

echo.
echo ================================================================================
echo 正在启动服务器...
echo ================================================================================
echo.
echo 📍 Backend URL:  http://localhost:8000
echo 📍 主页:         http://localhost:8000/
echo 📍 RPGv2 URL:    http://localhost:3000
echo 📍 API 文档:     http://localhost:8000/docs
echo.
echo 💡 提示:
echo    - Backend 日志将在此窗口显示
echo    - RPGv2 日志将在另一个窗口显示
echo    - 按 Ctrl+C 停止 Backend
echo    - 关闭窗口将停止对应服务
echo.
echo ================================================================================
echo.

REM 启动 RPGv2 Frontend（新窗口）
echo [+] 启动 RPGv2 Frontend...
start "AI 防诈骗平台 - RPGv2 Frontend" cmd /k "cd /d "%SCRIPT_DIR%..\rpg-platform-v2" && echo [RPGv2] 正在启动... && npm run dev"

REM 等待 Frontend 启动
echo [+] 等待 RPGv2 启动（5 秒）...
timeout /t 5 /nobreak >nul
echo.

REM 启动 Backend（当前窗口）
echo [+] 启动 Backend...
echo.
%PYTHON_CMD% scripts\start_server.py

pause
