@echo off
chcp 65001 > nul
cd /d "%~dp0"

REM 保存根目錄路徑（在任何 cd 之前），去掉結尾反斜線
set "ROOT_DIR=%~dp0"
if "%ROOT_DIR:~-1%"=="\" set "ROOT_DIR=%ROOT_DIR:~0,-1%"

echo ================================================================================
echo Starting AI Anti-Scam Platform Services
echo ================================================================================
echo.

REM 檢查是否啟用 Gemini
set GEMINI_ENABLED=true
if exist "%ROOT_DIR%\backend\.env" (
    for /f "tokens=2 delims==" %%a in ('findstr /i "^GEMINI_ENABLED" "%ROOT_DIR%\backend\.env"') do set GEMINI_ENABLED=%%a
)

echo [1/5] Checking data files...
if not exist "%ROOT_DIR%\data\scraped_alerts_lite.json" (
    echo [INFO] Creating lite version of scraped_alerts.json...
    py "%ROOT_DIR%\backend\scripts\create_lite_data.py"
    echo [OK] Lite data created
) else (
    echo [OK] Lite data exists
)
echo.

echo [2/5] Checking LLM Provider...
if /i "%GEMINI_ENABLED%"=="true" (
    echo [INFO] Gemini API mode enabled
    echo [INFO] Skipping file upload ^(RAG mode, no upload needed^)
) else (
    echo [INFO] Ollama mode enabled
    echo [INFO] Checking Ollama service...
    curl -s http://localhost:11434/api/tags >nul 2>&1
    if %errorlevel% neq 0 (
        echo [WARNING] Ollama service not running!
        echo [WARNING] Please start Ollama first: ollama serve
    ) else (
        echo [OK] Ollama service is running
    )
)
echo.

echo [3/5] Cleaning old processes...
taskkill /F /FI "WINDOWTITLE eq Backend Server" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq RPGv2 Frontend" >nul 2>&1
timeout /t 1 /nobreak >nul
echo [OK] Done
echo.

echo [4/5] Starting Backend (port 8000)...
REM 清除可能從 Docker 繼承的 stale env vars，確保 .env 生效
set OLLAMA_BASE_URL=
set OLLAMA_BASE_URL_SCAMMER=
set OLLAMA_BASE_URL_VICTIM=
set OLLAMA_BASE_URL_EXPERT=
set OLLAMA_BASE_URL_RECORDER=
set BACKEND_CMD=cd /d "%ROOT_DIR%" ^&^& call venv\Scripts\activate.bat ^&^& cd backend ^&^& set FORCE_GPU=0 ^&^& set OLLAMA_NUM_PREDICT_SCAMMER=200 ^&^& set USE_SIMPLE_PROMPTS=true ^&^& py main.py
start "Backend Server" cmd /k "%BACKEND_CMD%"
timeout /t 8 /nobreak >nul
echo [OK] Backend started
echo.

echo [5/5] Starting RPGv2 (port 3000)...
set RPGV2_CMD=cd /d "%ROOT_DIR%\rpg-platform-v2" ^&^& npm run dev
start "RPGv2 Frontend" /MIN cmd /c "%RPGV2_CMD%"
timeout /t 3 /nobreak >nul
echo [OK] RPGv2 started
echo.

echo ================================================================================
echo Services Started!
echo ================================================================================
echo.
if /i "%GEMINI_ENABLED%"=="true" (
    echo LLM Provider: Gemini API (gemini-3.1-flash-lite-preview)
) else (
    echo LLM Provider: Ollama (local)
)
echo Backend API:  http://localhost:8000
echo API Docs:     http://localhost:8000/docs
echo RPGv2:        http://localhost:3000
echo.
echo Press any key to check status...
pause >nul

echo.
echo Checking services...
echo.

netstat -ano | findstr ":8000.*LISTENING"
if %errorlevel% equ 0 (
    echo [OK] Backend is running on port 8000
) else (
    echo [!] Backend may not be running
)

netstat -ano | findstr ":3000.*LISTENING"
if %errorlevel% equ 0 (
    echo [OK] RPGv2 is running on port 3000
) else (
    echo [!] RPGv2 may not be running
)

echo.
echo Press any key to exit...
pause >nul
