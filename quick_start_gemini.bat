@echo off
chcp 65001 > nul
cd /d "%~dp0"

echo ================================================================================
echo AI Anti-Scam Platform - Gemini Mode Quick Start
echo ================================================================================
echo.

REM 檢查 .env 文件
if not exist backend\.env (
    echo [ERROR] backend\.env file not found!
    echo.
    echo Please create backend\.env with:
    echo   GEMINI_ENABLED=true
    echo   GEMINI_API_KEY=your_api_key_here
    echo   GEMINI_MODEL_SCAMMER=gemini-2.5-flash
    echo   GEMINI_MODEL_VICTIM=gemini-2.5-flash
    echo   GEMINI_MODEL_EXPERT=gemini-2.5-flash
    echo   GEMINI_MODEL_RECORDER=gemini-2.5-flash
    echo.
    pause
    exit /b 1
)

REM 檢查 API Key
findstr /i "GEMINI_API_KEY" backend\.env | findstr /v "your_api_key_here" >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] GEMINI_API_KEY not configured!
    echo.
    echo Please edit backend\.env and set your Gemini API Key
    echo Get your API key from: https://aistudio.google.com/app/apikey
    echo.
    pause
    exit /b 1
)

echo [1/6] Checking data files...
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

echo [2/6] Checking Gemini configuration...
echo [OK] API Key configured
echo.

echo [3/6] Initializing Gemini files...
cd backend
py scripts\init_gemini_files.py
if %errorlevel% neq 0 (
    echo [ERROR] File initialization failed!
    cd ..
    pause
    exit /b 1
)
cd ..
echo.

echo [4/6] Cleaning old processes...
taskkill /F /FI "WINDOWTITLE eq Backend*" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq RPGv2*" >nul 2>&1
timeout /t 1 /nobreak >nul
echo [OK] Done
echo.

echo [5/6] Starting Backend with Gemini (port 8000)...
cd backend
start "Backend Server (Gemini)" cmd /c "py -m uvicorn main:app --reload --port 8000"
cd ..
timeout /t 5 /nobreak >nul
echo [OK] Backend started
echo.

echo [6/6] Starting RPGv2 Frontend (port 3000)...
cd rpg-platform-v2
start "RPGv2 Frontend" /MIN cmd /c "npm run dev"
cd ..
timeout /t 3 /nobreak >nul
echo [OK] RPGv2 started
echo.

echo ================================================================================
echo Services Started Successfully!
echo ================================================================================
echo.
echo LLM Provider:  Gemini API (gemini-2.5-flash)
echo Backend API:   http://localhost:8000
echo API Docs:      http://localhost:8000/docs
echo RPGv2:         http://localhost:3000
echo.
echo Features:
echo   - System Instructions (4 Agent personas)
echo   - File API (Long Context with 30 optimized cases)
echo   - Real HK organizations database
echo   - 90%% reduced token usage (lite data)
echo.
echo Press any key to check status...
pause >nul

echo.
echo Checking services...
echo.

netstat -ano | findstr ":8000.*LISTENING" >nul
if %errorlevel% equ 0 (
    echo [OK] Backend is running on port 8000
) else (
    echo [!] Backend may not be running
    echo [!] Check the Backend Server window for errors
)

netstat -ano | findstr ":3000.*LISTENING" >nul
if %errorlevel% equ 0 (
    echo [OK] RPGv2 is running on port 3000
) else (
    echo [!] RPGv2 may not be running
    echo [!] Check the RPGv2 Frontend window for errors
)

echo.
echo ================================================================================
echo Quick Tips:
echo ================================================================================
echo.
echo 1. Click the Gemini toggle in the top-right corner to enable Gemini mode
echo 2. Files expire after 2 days - re-run this script to refresh
echo 3. Check backend logs for detailed information
echo.
echo Press any key to exit...
pause >nul
