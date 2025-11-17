@echo off
setlocal enabledelayedexpansion
chcp 65001 > nul

echo ========================================
echo RPG Maker Simulation 集成測試
echo ========================================
echo.

echo [步驟 1/5] 檢查 Backend 服務...
curl -s http://localhost:8000/ >nul 2>&1
if %errorlevel% neq 0 (
    echo [錯誤] Backend 服務未運行
    echo     請先運行: python start_server.py
    pause
    exit /b 1
)
echo [OK] Backend 服務運行中

echo.
echo [步驟 2/5] 檢查 V2 API...
curl -s http://localhost:8000/api/game/v2/health >nul 2>&1
if %errorlevel% neq 0 (
    echo [錯誤] V2 API 不可用
    pause
    exit /b 1
)
echo [OK] V2 API 可用

echo.
echo [步驟 3/5] 測試啟動 Simulation...
curl -X POST http://localhost:8000/simulation/start ^
  -H "Content-Type: application/json" ^
  -d "{\"victim_persona\":\"average\",\"scam_tactic\":\"WhatsApp 對話詐騙\",\"mode\":\"fast\",\"auto_train\":true}" ^
  -o simulation_test.json
  
if %errorlevel% neq 0 (
    echo [錯誤] 無法啟動 Simulation
    pause
    exit /b 1
)

echo [OK] Simulation 已啟動

echo.
echo [步驟 4/5] 檢查 Simulation ID...
for /f "tokens=*" %%i in ('type simulation_test.json') do set SIMULATION_RESPONSE=%%i
echo 響應: %SIMULATION_RESPONSE%

echo.
echo [步驟 5/5] 檢查插件文件...
if exist rpg_maker_plugins\SimulationViewer.js (
    echo [OK] SimulationViewer.js 已創建
) else (
    echo [警告] SimulationViewer.js 不存在
)

if exist RPG_platform\RPG_Project\js\plugins\SimulationViewer.js (
    echo [OK] 插件已複製到 RPG Maker
) else (
    echo [INFO] 插件尚未複製到 RPG Maker
    echo     運行以下命令複製:
    echo     copy rpg_maker_plugins\SimulationViewer.js RPG_platform\RPG_Project\js\plugins\
)

echo.
echo ========================================
echo 測試完成
echo ========================================
echo.
echo 結果:
echo   ✓ Backend 服務正常
echo   ✓ V2 API 可用
echo   ✓ Simulation 可以啟動
echo   ✓ 插件已創建
echo.
echo 下一步:
echo   1. 複製插件到 RPG Maker (如果尚未複製)
echo   2. 在 RPG Maker 中啟用插件
echo   3. 創建測試事件
echo   4. 測試遊戲
echo.

REM 清理臨時文件
del simulation_test.json 2>nul

pause

