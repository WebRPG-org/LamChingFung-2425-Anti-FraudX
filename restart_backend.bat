@echo off
echo ============================================================
echo   重啟後端服務
echo ============================================================

echo.
echo [1] 停止舊的後端進程...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq Backend*" 2>nul
taskkill /F /IM py.exe /FI "WINDOWTITLE eq Backend*" 2>nul
timeout /t 2 /nobreak >nul
echo [OK] 舊進程已停止

echo.
echo [2] 啟動新的後端服務...
cd /d "%~dp0backend"
start "Backend Server" py main.py
timeout /t 3 /nobreak >nul

echo.
echo [3] 檢查服務狀態...
timeout /t 2 /nobreak >nul
netstat -ano | findstr ":8000" >nul
if %errorlevel% equ 0 (
    echo [OK] 後端服務已啟動在 http://localhost:8000
) else (
    echo [!] 後端服務可能未啟動，請檢查
)

echo.
echo ============================================================
echo   後端服務已重啟
echo ============================================================
echo.
echo 測試 API: http://localhost:8000/docs
echo.
pause
