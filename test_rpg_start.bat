@echo off
chcp 65001 > nul

echo ================================================================================
echo 測試 RPGv2 啟動
echo ================================================================================
echo.

cd /d "%~dp0"

echo [1] 檢查 RPGv2 目錄...
if exist "rpg-platform-v2" (
    echo [OK] RPGv2 目錄存在
) else (
    echo [X] RPGv2 目錄不存在
    pause
    exit /b 1
)
echo.

echo [2] 檢查 package.json...
if exist "rpg-platform-v2\package.json" (
    echo [OK] package.json 存在
) else (
    echo [X] package.json 不存在
    pause
    exit /b 1
)
echo.

echo [3] 檢查 node_modules...
if exist "rpg-platform-v2\node_modules" (
    echo [OK] node_modules 存在
) else (
    echo [!] node_modules 不存在，正在安裝...
    cd rpg-platform-v2
    npm install
    cd ..
)
echo.

echo [4] 啟動 RPGv2 服務（前台模式，用於調試）...
echo.
cd rpg-platform-v2
npm run dev
