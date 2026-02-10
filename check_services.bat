@echo off
chcp 65001 >nul
echo ========================================
echo   AI-Agentv4 服務狀態
echo ========================================
echo.

echo [Backend 服務狀態]
tasklist /FI "WINDOWTITLE eq Backend*" /V 2>nul | find "Backend" >nul
if %ERRORLEVEL% EQU 0 (
    echo ✅ Backend 正在運行
    echo.
    echo 進程詳情：
    tasklist /FI "WINDOWTITLE eq Backend*" /V | findstr "python"
) else (
    echo ❌ Backend 未運行
)

echo.
echo ========================================
echo.

echo [Vite 服務狀態]
tasklist /FI "WINDOWTITLE eq Vite*" /V 2>nul | find "Vite" >nul
if %ERRORLEVEL% EQU 0 (
    echo ✅ Vite 正在運行
    echo.
    echo 進程詳情：
    tasklist /FI "WINDOWTITLE eq Vite*" /V | findstr "node"
) else (
    echo ❌ Vite 未運行
)

echo.
echo ========================================
echo.

echo [端口佔用情況]
echo.
echo Backend (8000):
netstat -ano | findstr ":8000" | findstr "LISTENING"
if %ERRORLEVEL% NEQ 0 echo   未佔用

echo.
echo Vite (3000):
netstat -ano | findstr ":3000" | findstr "LISTENING"
if %ERRORLEVEL% NEQ 0 echo   未佔用

echo.
echo ========================================
echo.
pause
