@echo off
chcp 65001 >nul
echo ========================================
echo   AI-Agentv4 服務啟動腳本
echo ========================================
echo.

REM 檢查是否已經在運行
echo [1/3] 檢查現有服務...
tasklist /FI "IMAGENAME eq python.exe" /FI "WINDOWTITLE eq Backend*" 2>NUL | find /I /N "python.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo ⚠️  Backend 已在運行
) else (
    echo ✅ Backend 未運行
)

tasklist /FI "IMAGENAME eq node.exe" /FI "WINDOWTITLE eq Vite*" 2>NUL | find /I /N "node.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo ⚠️  Vite 已在運行
) else (
    echo ✅ Vite 未運行
)

echo.
echo [2/3] 啟動 Backend 服務（背景運行）...
start "Backend Server" /MIN cmd /c "cd /d %~dp0backend && py main.py"
timeout /t 3 /nobreak >nul
echo ✅ Backend 已啟動（端口 8000）

echo.
echo [3/3] 啟動 Vite 前端服務（背景運行）...
start "Vite Dev Server" /MIN cmd /c "cd /d %~dp0 && npm run dev"
timeout /t 3 /nobreak >nul
echo ✅ Vite 已啟動（端口 5173）

echo.
echo ========================================
echo   🎉 所有服務已啟動！
echo ========================================
echo.
echo 📍 服務地址：
echo    - Frontend: http://localhost:3000
echo    - Backend:  http://localhost:8000
echo    - API Docs: http://localhost:8000/docs
echo.
echo 💡 提示：
echo    - 服務在背景運行，關閉此窗口不影響服務
echo    - 使用 stop_services.bat 停止所有服務
echo    - 使用 view_logs.bat 查看服務日誌
echo.
pause
