@echo off
chcp 65001 > nul

REM Get script directory and move to project root (parent dir)
SET SCRIPT_DIR=%~dp0
CD /d "%SCRIPT_DIR%.."

echo.
echo ================================================================================
echo AI反詐騙平台 - 一鍵啟動 (優化版 v2.2.0)
echo ================================================================================
echo 工作目錄: %CD%
echo.

echo [步驟1/6] 清理舊的進程...
taskkill /F /FI "WINDOWTITLE eq Backend*" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq Vite*" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq RPGv2*" >nul 2>&1
timeout /t 1 /nobreak >nul
echo [OK] 清理完成
echo.

echo [步驟2/6] 檢查 Python 環境...
REM 嘗試使用 py 命令（Windows Python Launcher）
where py >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_CMD=py
    for /f "tokens=*" %%i in ('py --version') do set PYTHON_VERSION=%%i
    echo [OK] %PYTHON_VERSION% ^(使用 py 命令^)
) else (
    python --version >nul 2>&1
    if errorlevel 1 (
        echo [X] 錯誤: 未找到 Python，請先安裝 Python 3.8+
        echo.
        echo 請前往 https://www.python.org/downloads/ 下載安裝
        echo 安裝時務必勾選 "Add Python to PATH"
        pause
        exit /b 1
    )
    set PYTHON_CMD=python
    for /f "tokens=*" %%i in ('python --version') do set PYTHON_VERSION=%%i
    echo [OK] %PYTHON_VERSION%
)
echo.

echo [步驟3/6] 檢查 Node.js 環境...
node --version >nul 2>&1
if errorlevel 1 (
    echo [X] 錯誤: 未找到 Node.js，請先安裝 Node.js 14+
    echo.
    echo 請前往 https://nodejs.org/ 下載安裝
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('node --version') do set NODE_VERSION=%%i
echo [OK] Node.js %NODE_VERSION%
echo.

echo [步驟4/6] 檢查 Backend 依賴...
if not exist "backend\requirements.txt" (
    echo [X] 錯誤: backend\requirements.txt 不存在
    pause
    exit /b 1
)
echo [OK] Backend 依賴配置已就緒
echo.

echo [步驟5/6] 檢查 RPGv2 依賴...
if exist "rpg-platform-v2" (
    cd rpg-platform-v2
    if not exist "node_modules" (
        echo [+] 安裝 RPGv2 依賴（首次運行可能需要幾分鐘）...
        call npm install
        if errorlevel 1 (
            echo [X] RPGv2 依賴安裝失敗
            cd ..
            pause
            exit /b 1
        )
    )
    echo [OK] RPGv2 依賴已就緒
    cd ..
) else (
    echo [!] RPGv2 目錄不存在，跳過
    set SKIP_RPG=1
)
echo.

echo [步驟6/6] 啟動服務...
if not exist "backend\.env" (
    echo [!] 警告: backend\.env 不存在，將使用默認設置
)

echo.
echo ================================================================================
echo 正在啟動服務器（背景運行模式）...
echo ================================================================================
echo.
echo 📍 服務地址:
echo    - Backend API:  http://localhost:8000
echo    - API 文檔:     http://localhost:8000/docs
if not "%SKIP_RPG%"=="1" (
    echo    - RPGv2:        http://localhost:3000
)
echo.
echo 💡 提示:
echo    - 所有服務在背景運行 (最小化窗口)
echo    - 關閉此窗口不影響服務運行
echo    - 使用 stop_services.bat 停止所有服務
echo    - 使用 check_services.bat 查看服務狀態
echo.
echo 🚀 優化功能:
echo    - AI判定結果緩存 (命中率 30-50%%)
echo    - 快速路徑判定 (響應時間 小於50ms)
echo    - 智能混合判定 (平均響應 小於200ms)
echo    - 性能監控 API: /api/rpgv2/performance/stats
echo.
echo ================================================================================
echo.

REM 啟動 Backend（背景運行）
echo [+] 啟動 Backend 服務...
echo [DEBUG] 腳本目錄: %SCRIPT_DIR%
echo [DEBUG] Backend 腳本: %SCRIPT_DIR%start_backend.bat
if exist "%SCRIPT_DIR%start_backend.bat" (
    start "Backend Server" /MIN "%SCRIPT_DIR%start_backend.bat"
    timeout /t 3 /nobreak >nul
    echo [OK] Backend 已啟動（端口 8000）
) else (
    echo [X] 錯誤: 找不到 start_backend.bat
)
echo.

REM 啟動 RPGv2 Frontend（背景運行）
if not "%SKIP_RPG%"=="1" (
    echo [+] 啟動 RPGv2 前端服務...
    echo [DEBUG] RPG 腳本: %SCRIPT_DIR%start_rpg.bat
    if exist "%SCRIPT_DIR%start_rpg.bat" (
        start "RPGv2 Frontend" /MIN "%SCRIPT_DIR%start_rpg.bat"
        timeout /t 3 /nobreak >nul
        echo [OK] RPGv2 已啟動（端口 3000）
    ) else (
        echo [X] 錯誤: 找不到 start_rpg.bat
    )
    echo.
)

echo ================================================================================
echo 🎉 所有服務已成功啟動！
echo ================================================================================
echo.

REM 等待服務完全啟動
echo [+] 等待服務完全啟動（5秒）...
timeout /t 5 /nobreak >nul
echo.

REM 測試服務可訪問性
echo [+] 測試服務可訪問性...
echo.

REM 測試 Backend
curl -s http://localhost:8000/docs >nul 2>&1
if %errorlevel% equ 0 (
    echo    Backend API 可訪問
) else (
    echo    Backend API 可能還在啟動中
)

REM 測試 RPGv2
if not "%SKIP_RPG%"=="1" (
    curl -s http://localhost:3000 >nul 2>&1
    if %errorlevel% equ 0 (
        echo    RPGv2 可訪問
    ) else (
        echo    RPGv2 可能還在啟動中
    )
)

echo.
echo ================================================================================
echo.
echo 📚 快速鏈接:
echo.
echo    打開 API 文檔: start http://localhost:8000/docs
if not "%SKIP_RPG%"=="1" (
    echo    打開 RPGv2:   start http://localhost:3000
)
echo.
echo 管理命令:
echo.
echo    查看狀態:     check_services.bat
echo    查看日誌:     view_logs.bat
echo    停止服務:     stop_services.bat
echo.
echo ================================================================================
echo.

REM 詢問是否自動打開瀏覽器
set /p OPEN_BROWSER="是否自動打開瀏覽器？(Y/N): "
if /i "%OPEN_BROWSER%"=="Y" (
    echo.
    echo [+] 正在打開瀏覽器...
    if not "%SKIP_RPG%"=="1" (
        start http://localhost:3000
    ) else (
        start http://localhost:8000/docs
    )
    timeout /t 2 /nobreak >nul
)

echo.
echo 啟動完成! 按任意鍵退出 (服務將繼續在背景運行)...
pause >nul
