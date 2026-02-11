@echo off
REM Quick deployment script for Windows

echo ========================================
echo Hong Kong Anti-Scam RPG - Quick Deployment
echo ========================================
echo.

REM Check if Ansible is installed
where ansible >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Ansible is not installed. Installing...
    pip install ansible
)

REM Check if inventory exists
if not exist "inventory\hosts.yml" (
    echo Inventory file not found. Please configure inventory\hosts.yml first.
    exit /b 1
)

REM Parse arguments
set PLAYBOOK=site.yml
set EXTRA_ARGS=

:parse_args
if "%~1"=="" goto run_playbook
if "%~1"=="--frontend" (
    set PLAYBOOK=frontend.yml
    shift
    goto parse_args
)
if "%~1"=="--backend" (
    set PLAYBOOK=backend.yml
    shift
    goto parse_args
)
if "%~1"=="--dev" (
    set PLAYBOOK=dev-setup.yml
    shift
    goto parse_args
)
if "%~1"=="--update" (
    set PLAYBOOK=update.yml
    shift
    goto parse_args
)
if "%~1"=="--check" (
    set EXTRA_ARGS=%EXTRA_ARGS% --check
    shift
    goto parse_args
)
if "%~1"=="--verbose" (
    set EXTRA_ARGS=%EXTRA_ARGS% -vvv
    shift
    goto parse_args
)

:run_playbook
echo Running playbook: %PLAYBOOK%
echo.

ansible-playbook -i inventory\hosts.yml playbooks\%PLAYBOOK% %EXTRA_ARGS%

echo.
echo Deployment completed!
echo.
echo Next steps:
echo 1. Check the application status
echo 2. Configure DNS if needed
echo 3. Set up SSL certificates
echo 4. Monitor logs

pause
