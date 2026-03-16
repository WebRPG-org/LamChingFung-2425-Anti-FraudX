@echo off
chcp 65001 > nul
cd /d "%~dp0"

echo ================================================================================
echo AI-Agent v4 - Environment Setup (Windows)
echo ================================================================================
echo.

REM Check Python installation
echo [1/6] Checking Python installation...
py --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found!
    echo [ERROR] Please install Python 3.8 or higher from https://www.python.org/
    pause
    exit /b 1
)
py --version
echo [OK] Python found
echo.

REM Create virtual environment
echo [2/6] Creating virtual environment...
if exist "venv\" (
    echo [INFO] Virtual environment already exists
    set /p RECREATE="Do you want to recreate it? (y/n): "
    if /i "%RECREATE%"=="y" (
        echo [INFO] Removing existing virtual environment...
        rmdir /s /q venv
        echo [INFO] Creating new virtual environment...
        py -m venv venv
        echo [OK] Virtual environment recreated
    ) else (
        echo [OK] Using existing virtual environment
    )
) else (
    py -m venv venv
    echo [OK] Virtual environment created
)
echo.

REM Activate virtual environment
echo [3/6] Activating virtual environment...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo [ERROR] Failed to activate virtual environment
    pause
    exit /b 1
)
echo [OK] Virtual environment activated
echo.

REM Upgrade pip
echo [4/6] Upgrading pip...
python -m pip install --upgrade pip
echo [OK] Pip upgraded
echo.

REM Install dependencies
echo [5/6] Installing dependencies...
if not exist "backend\requirements.txt" (
    echo [ERROR] backend\requirements.txt not found!
    pause
    exit /b 1
)
pip install -r backend\requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)
echo [OK] Dependencies installed
echo.

REM Check and create .env file
echo [6/6] Checking environment configuration...
if not exist "backend\.env" (
    echo [INFO] Creating backend\.env file...
    (
        echo # AI-Agent v4 - Environment Configuration
        echo # LLM Provider Selection
        echo GEMINI_ENABLED=false
        echo.
        echo # Gemini API Configuration ^(if GEMINI_ENABLED=true^)
        echo GEMINI_API_KEY=your_gemini_api_key_here
        echo.
        echo # Ollama Configuration ^(if GEMINI_ENABLED=false^)
        echo OLLAMA_HOST=http://localhost:11434
        echo.
        echo # Application Settings
        echo DEBUG=false
        echo LOG_LEVEL=INFO
        echo USE_SIMPLE_PROMPTS=true
        echo FORCE_GPU=0
        echo.
        echo # Ollama Model Settings
        echo OLLAMA_NUM_PREDICT_SCAMMER=200
        echo.
        echo # RAG System Configuration
        echo RAG_COLLECTION_NAME=scam_cases
        echo RAG_SIMILARITY_THRESHOLD=10.0
        echo RAG_MAX_RESULTS=5
        echo.
        echo # Server Configuration
        echo HOST=0.0.0.0
        echo PORT=8000
    ) > backend\.env
    echo [OK] Created backend\.env
    echo [WARNING] Please edit backend\.env to configure your settings
) else (
    echo [OK] backend\.env exists
)
echo.

REM Check data files
if not exist "data\scraped_alerts_lite.json" (
    echo [INFO] scraped_alerts_lite.json not found
    echo [INFO] It will be created when you run quick_start.bat
) else (
    echo [OK] scraped_alerts_lite.json exists
)
echo.

echo ================================================================================
echo Setup completed successfully!
echo ================================================================================
echo.
echo Next Steps:
echo.
echo 1. Configure your environment:
echo    Edit backend\.env and set:
echo    - GEMINI_ENABLED=true ^(for Gemini API^)
echo    - GEMINI_API_KEY=your_actual_key
echo    OR
echo    - GEMINI_ENABLED=false ^(for Ollama^)
echo.
echo 2. Start the application:
echo    Double-click: quick_start.bat
echo.
echo 3. Access the services:
echo    Backend API:  http://localhost:8000
echo    API Docs:     http://localhost:8000/docs
echo    RPGv2:        http://localhost:3000
echo.
echo Press any key to exit...
pause >nul
