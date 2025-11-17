@echo off
chcp 65001 >nul
echo ========================================
echo 🚀 RPG Maker 訓練系統一鍵升級
echo ========================================
echo.
echo 此腳本將：
echo 1. 複製新插件到 RPG Maker 項目
echo 2. 備份舊插件
echo 3. 顯示後續步驟
echo.
pause

echo.
echo [步驟 1/3] 備份舊插件...
echo ----------------------------------------

set RPG_PLUGINS_DIR=RPG_platform\RPG_Project\js\plugins

if exist "%RPG_PLUGINS_DIR%\RotatingScamSystem.js" (
    echo 找到舊插件：RotatingScamSystem.js
    copy "%RPG_PLUGINS_DIR%\RotatingScamSystem.js" "%RPG_PLUGINS_DIR%\RotatingScamSystem.js.backup" >nul
    echo ✅ 已備份到：RotatingScamSystem.js.backup
) else (
    echo ⚠️  未找到舊插件（可能已移除）
)

echo.
echo [步驟 2/3] 複製新插件...
echo ----------------------------------------

if not exist "%RPG_PLUGINS_DIR%" (
    echo ❌ 錯誤：找不到 RPG Maker 插件目錄
    echo    請確認項目路徑：%RPG_PLUGINS_DIR%
    pause
    exit /b 1
)

echo 複製兼容版本插件...
copy "rpg_maker_plugins\SimulationTraining_Compatible.js" "%RPG_PLUGINS_DIR%\" >nul
if %errorlevel% equ 0 (
    echo ✅ SimulationTraining_Compatible.js 已複製
) else (
    echo ❌ 複製失敗
    pause
    exit /b 1
)

echo.
echo 複製其他版本插件（可選）...
copy "rpg_maker_plugins\SimulationTraining.js" "%RPG_PLUGINS_DIR%\" >nul
echo ✅ SimulationTraining.js 已複製

copy "rpg_maker_plugins\SimulationTraining_WithNPC.js" "%RPG_PLUGINS_DIR%\" >nul
echo ✅ SimulationTraining_WithNPC.js 已複製

echo.
echo [步驟 3/3] 檢查後端服務...
echo ----------------------------------------

curl -s http://localhost:8000/docs >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ 後端服務正在運行
) else (
    echo ⚠️  後端服務未運行
    echo    請先啟動後端：
    echo    cd backend
    echo    python main.py
)

echo.
echo ========================================
echo ✅ 插件複製完成！
echo ========================================
echo.
echo 📋 下一步操作：
echo.
echo 1. 打開 RPG Maker 編輯器
echo 2. 工具 → 插件管理器
echo 3. 禁用「RotatingScamSystem」
echo 4. 啟用「SimulationTraining_Compatible」
echo 5. 保存項目
echo 6. 測試遊戲（F12）
echo.
echo 📚 詳細使用指南：
echo    - RPG_Maker_兼容版本_使用指南.md
echo    - RPG_Maker_新訓練系統使用指南.md
echo.
echo 🎮 插件對比：
echo.
echo    SimulationTraining_Compatible.js  ⭐推薦！
echo    └─ 完全兼容原有設置，零修改升級
echo.
echo    SimulationTraining.js
echo    └─ 純後台訓練，不需要 NPC
echo.
echo    SimulationTraining_WithNPC.js
echo    └─ 需要重新設置 NPC
echo.
pause

