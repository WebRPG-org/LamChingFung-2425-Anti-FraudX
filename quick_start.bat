@echo off
chcp 65001 > nul
cd /d "%~dp0"

echo ================================================================================
echo Starting AI Anti-Scam Platform Services
echo ================================================================================
echo.

echo [1/3] Cleaning old processes...
taskkill /F /FI "WINDOWTITLE eq Backend*" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq RPGv2*" >nul 2>&1
timeout /t 1 /nobreak >nul
echo [OK] Done
echo.

echo [2/3] Starting Backend (port 8000)...
start "Backend Server" /MIN cmd /c "cd /d "%~dp0backend" && set FORCE_GPU=0 && set OLLAMA_NUM_PREDICT_SCAMMER=200 && set USE_SIMPLE_PROMPTS=true && py main.py"
timeout /t 3 /nobreak >nul
echo [OK] Backend started
echo.

echo [3/3] Starting RPGv2 (port 3000)...
start "RPGv2 Frontend" /MIN cmd /c "cd /d "%~dp0rpg-platform-v2" && npm run dev"
timeout /t 3 /nobreak >nul
echo [OK] RPGv2 started
echo.

echo ================================================================================
echo Services Started!
echo ================================================================================
echo.
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
