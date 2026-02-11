@echo off
chcp 65001 >nul
echo ========================================
echo   查看服務日誌
echo ========================================
echo.
echo 請選擇要查看的日誌：
echo.
echo [1] Backend 日誌
echo [2] Vite 日誌
echo [3] 同時查看兩個日誌
echo [0] 退出
echo.
set /p choice="請輸入選項 (0-3): "

if "%choice%"=="1" goto backend
if "%choice%"=="2" goto vite
if "%choice%"=="3" goto both
if "%choice%"=="0" goto end
goto end

:backend
echo.
echo ========================================
echo   Backend 日誌
echo ========================================
echo.
if exist "%~dp0backend\logs\app.log" (
    type "%~dp0backend\logs\app.log"
) else (
    echo ⚠️  日誌文件不存在
)
echo.
pause
goto end

:vite
echo.
echo ========================================
echo   Vite 日誌
echo ========================================
echo.
echo ℹ️  Vite 日誌在終端窗口中顯示
echo    請查看標題為 "Vite Dev Server" 的窗口
echo.
pause
goto end

:both
echo.
echo ========================================
echo   Backend 日誌
echo ========================================
echo.
if exist "%~dp0backend\logs\app.log" (
    type "%~dp0backend\logs\app.log"
) else (
    echo ⚠️  Backend 日誌文件不存在
)
echo.
echo ========================================
echo   Vite 日誌
echo ========================================
echo.
echo ℹ️  Vite 日誌在終端窗口中顯示
echo    請查看標題為 "Vite Dev Server" 的窗口
echo.
pause
goto end

:end
