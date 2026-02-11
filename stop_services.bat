@echo off
chcp 65001 >nul
echo ========================================
echo   停止 AI-Agentv4 服務
echo ========================================
echo.

echo [1/2] 停止 Backend 服務...
taskkill /FI "WINDOWTITLE eq Backend*" /F >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo ✅ Backend 已停止
) else (
    echo ⚠️  Backend 未運行或已停止
)

echo.
echo [2/2] 停止 Vite 服務...
taskkill /FI "WINDOWTITLE eq Vite*" /F >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo ✅ Vite 已停止
) else (
    echo ⚠️  Vite 未運行或已停止
)

REM 額外清理：停止所有相關的 node 和 python 進程（可選）
echo.
echo [額外] 清理殘留進程...
for /f "tokens=2" %%a in ('tasklist /FI "IMAGENAME eq python.exe" /FO LIST ^| find "PID:"') do (
    tasklist /FI "PID eq %%a" /V | find "main.py" >nul 2>&1
    if not errorlevel 1 (
        taskkill /PID %%a /F >nul 2>&1
        echo ✅ 已停止 Python 進程 (PID: %%a)
    )
)

for /f "tokens=2" %%a in ('tasklist /FI "IMAGENAME eq node.exe" /FO LIST ^| find "PID:"') do (
    tasklist /FI "PID eq %%a" /V | find "vite" >nul 2>&1
    if not errorlevel 1 (
        taskkill /PID %%a /F >nul 2>&1
        echo ✅ 已停止 Node 進程 (PID: %%a)
    )
)

echo.
echo ========================================
echo   🎉 所有服務已停止！
echo ========================================
echo.
pause
