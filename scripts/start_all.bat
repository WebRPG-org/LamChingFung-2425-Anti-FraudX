@echo off
chcp 65001 > nul

REM Get script directory and move to project root (parent dir)
SET SCRIPT_DIR=%~dp0
CD /d "%SCRIPT_DIR%.."

echo.
echo ================================================================================
echo AI Anti-Scam Platform - Start All Services (v2.2.2)
echo ================================================================================
echo Working Directory: %CD%
echo.

echo [Step 1/6] Cleaning old processes...
taskkill /F /FI "WINDOWTITLE eq Backend*" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq Vite*" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq RPGv2*" >nul 2>&1
timeout /t 1 /nobreak >nul
echo [OK] Cleanup complete
echo.

echo [Step 2/6] Checking Python environment...
where py >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_CMD=py
    echo [OK] Python found (using py command)
) else (
    where python >nul 2>&1
    if %errorlevel% equ 0 (
        set PYTHON_CMD=python
        echo [OK] Python found (using python command)
    ) else (
        echo [X] Error: Python not found
        pause
        exit /b 1
    )
)
echo.

echo [Step 3/6] Checking Node.js environment...
where node >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Node.js found
) else (
    echo [X] Error: Node.js not found
    pause
    exit /b 1
)
echo.

echo [Step 4/6] Checking Backend dependencies...
if not exist "backend\requirements.txt" (
    echo [X] Error: backend\requirements.txt not found
    pause
    exit /b 1
)
echo [OK] Backend dependencies ready
echo.

echo [Step 5/6] Checking RPGv2 dependencies...
if exist "rpg-platform-v2" (
    cd rpg-platform-v2
    if not exist "node_modules" (
        echo [+] Installing RPGv2 dependencies...
        call npm install
        if errorlevel 1 (
            echo [X] RPGv2 dependency installation failed
            cd ..
            pause
            exit /b 1
        )
    )
    echo [OK] RPGv2 dependencies ready
    cd ..
) else (
    echo [!] RPGv2 directory not found, skipping
    set SKIP_RPG=1
)
echo.

echo [Step 6/6] Starting services...
echo.
echo ================================================================================
echo Starting servers (background mode)...
echo ================================================================================
echo.
echo Service URLs:
echo    - Backend API:  http://localhost:8000
echo    - API Docs:     http://localhost:8000/docs
if not "%SKIP_RPG%"=="1" (
    echo    - RPGv2:        http://localhost:3000
)
echo.
echo ================================================================================
echo.

REM Start Backend
echo [+] Starting Backend service...
echo [DEBUG] Script directory: %SCRIPT_DIR%
echo [DEBUG] Backend script: %SCRIPT_DIR%start_backend.bat
if exist "%SCRIPT_DIR%start_backend.bat" (
    start "Backend Server" /MIN "%SCRIPT_DIR%start_backend.bat"
    timeout /t 3 /nobreak >nul
    echo [OK] Backend started (port 8000)
) else (
    echo [X] Error: start_backend.bat not found
)
echo.

REM Start RPGv2
if not "%SKIP_RPG%"=="1" (
    echo [+] Starting RPGv2 frontend service...
    echo [DEBUG] RPG script: %SCRIPT_DIR%start_rpg.bat
    if exist "%SCRIPT_DIR%start_rpg.bat" (
        start "RPGv2 Frontend" /MIN "%SCRIPT_DIR%start_rpg.bat"
        timeout /t 3 /nobreak >nul
        echo [OK] RPGv2 started (port 3000)
    ) else (
        echo [X] Error: start_rpg.bat not found
    )
    echo.
)

echo ================================================================================
echo All services started!
echo ================================================================================
echo.

REM Wait for services to fully start
echo [+] Waiting for services to fully start (5 seconds)...
timeout /t 5 /nobreak >nul
echo.

REM Test service accessibility
echo [+] Testing service accessibility...
echo.

REM Test Backend
curl -s http://localhost:8000/docs >nul 2>&1
if %errorlevel% equ 0 (
    echo    Backend API accessible
) else (
    echo    Backend API may still be starting...
)

REM Test RPGv2
if not "%SKIP_RPG%"=="1" (
    curl -s http://localhost:3000 >nul 2>&1
    if %errorlevel% equ 0 (
        echo    RPGv2 accessible
    ) else (
        echo    RPGv2 may still be starting...
    )
)

echo.
echo ================================================================================
echo.
echo Quick Links:
echo.
echo    Open API Docs: start http://localhost:8000/docs
if not "%SKIP_RPG%"=="1" (
    echo    Open RPGv2:    start http://localhost:3000
)
echo.
echo Management Commands:
echo.
echo    Check status:  check_services.bat
echo    View logs:     view_logs.bat
echo    Stop services: stop_services.bat
echo.
echo ================================================================================
echo.

REM Ask to open browser
set /p OPEN_BROWSER="Open browser automatically? (Y/N): "
if /i "%OPEN_BROWSER%"=="Y" (
    echo.
    echo [+] Opening browser...
    if not "%SKIP_RPG%"=="1" (
        start http://localhost:3000
    ) else (
        start http://localhost:8000/docs
    )
    timeout /t 2 /nobreak >nul
)

echo.
echo Startup complete! Press any key to exit (services will continue running)...
pause >nul
