@echo off
chcp 65001 > nul
cd /d "%~dp0"

echo ================================================================================
echo Starting AI Anti-Scam Platform Services
echo ================================================================================
echo.

REM 檢查是否啟用 Gemini
set GEMINI_ENABLED=false
if exist backend\.env (
    for /f "tokens=2 delims==" %%a in ('findstr /i "^GEMINI_ENABLED" backend\.env') do set GEMINI_ENABLED=%%a
)

echo [1/5] Checking data files...
if not exist "data\scraped_alerts_lite.json" (
    echo [INFO] Creating lite version of scraped_alerts.json...
    cd backend
    py scripts\create_lite_data.py
    cd ..
    echo [OK] Lite data created
) else (
    echo [OK] Lite data exists
)
echo.

echo [2/5] Checking LLM Provider...
if /i "%GEMINI_ENABLED%"=="true" (
    echo [INFO] Gemini API mode enabled
    echo [INFO] Checking Gemini files...
    cd backend
    py scripts\init_gemini_files.py
    cd ..
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
taskkill /F /FI "WINDOWTITLE eq Backend*" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq RPGv2*" >nul 2>&1
timeout /t 1 /nobreak >nul
echo [OK] Done
echo.

echo [4/5] Starting Backend (port 8000)...
cd backend
start "Backend Server" /MIN cmd /c "set FORCE_GPU=0 && set OLLAMA_NUM_PREDICT_SCAMMER=200 && set USE_SIMPLE_PROMPTS=true && py main.py"
cd ..
timeout /t 3 /nobreak >nul
echo [OK] Backend started
echo.

echo [5/5] Starting RPGv2 (port 3000)...
cd rpg-platform-v2
start "RPGv2 Frontend" /MIN cmd /c "npm run dev"
cd ..
timeout /t 3 /nobreak >nul
echo [OK] RPGv2 started
echo.

echo ================================================================================
echo Services Started!
echo ================================================================================
echo.
if /i "%GEMINI_ENABLED%"=="true" (
    echo LLM Provider: Gemini API (gemini-2.5-flash)
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
