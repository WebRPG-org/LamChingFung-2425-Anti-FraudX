@echo off
setlocal enabledelayedexpansion
chcp 65001 > nul

echo ========================================
echo 創建離線部署包
echo ========================================
echo.

REM 創建部署包目錄
set DATE_STR=%date:~0,4%%date:~5,2%%date:~8,2%
set TIME_STR=%time:~0,2%%time:~3,2%%time:~6,2%
set TIME_STR=!TIME_STR: =0!
set PACKAGE_DIR=deployment_package_%DATE_STR%_%TIME_STR%

echo [1/6] 創建目錄結構...
if exist %PACKAGE_DIR% (
    echo [警告] 目錄已存在，將刪除舊目錄
    rmdir /S /Q %PACKAGE_DIR%
)
mkdir %PACKAGE_DIR%
mkdir %PACKAGE_DIR%\models
mkdir %PACKAGE_DIR%\code
mkdir %PACKAGE_DIR%\config
mkdir %PACKAGE_DIR%\scripts
mkdir %PACKAGE_DIR%\docs

echo [2/6] 導出 Fine-Tuned 模型...
echo     這可能需要幾分鐘...
if exist models\expert_model.tar (
    echo     [跳過] expert_model.tar 已存在
) else (
    echo     導出專家模型...
    ollama save anti-fraud-expert-20251111_220455 -o %PACKAGE_DIR%\models\expert_model.tar
    if !errorlevel! equ 0 (
        echo     [OK] 專家模型導出成功
    ) else (
        echo     [錯誤] 專家模型導出失敗
    )
)

if exist models\scammer_model.tar (
    echo     [跳過] scammer_model.tar 已存在
) else (
    echo     導出騙徒模型...
    ollama save anti-fraud-scammer-20251111_220455 -o %PACKAGE_DIR%\models\scammer_model.tar
    if !errorlevel! equ 0 (
        echo     [OK] 騙徒模型導出成功
    ) else (
        echo     [錯誤] 騙徒模型導出失敗
    )
)

echo     導出基礎模型...
ollama save gemma3:4b -o %PACKAGE_DIR%\models\gemma3_4b_base.tar
if !errorlevel! equ 0 (
    echo     [OK] 基礎模型導出成功
) else (
    echo     [警告] 基礎模型導出失敗（可能已存在）
)

echo [3/6] 複製項目代碼...
echo     複製 backend...
xcopy /E /I /Y /EXCLUDE:exclude_list.txt backend %PACKAGE_DIR%\code\backend >nul 2>&1

echo     複製 frontend...
if exist frontend (
    xcopy /E /I /Y frontend %PACKAGE_DIR%\code\frontend >nul 2>&1
)

echo     複製啟動文件...
copy start_server.py %PACKAGE_DIR%\code\ 2>nul
copy backend\requirements.txt %PACKAGE_DIR%\code\ 2>nul

echo [4/6] 創建配置模板...
(
echo # ============================================
echo # 離線部署配置（數據完全隔離）
echo # ============================================
echo.
echo # Agent 模型配置（使用 Fine-Tuned 模型）
echo AGENT_MODEL_EXPERT=anti-fraud-expert-20251111_220455
echo AGENT_MODEL_SCAMMER=anti-fraud-scammer-20251111_220455
echo AGENT_MODEL=gemma3:4b
echo.
echo # Ollama 配置（只監聽本地，確保數據不流出）
echo OLLAMA_BASE_URL=http://127.0.0.1:11434
echo.
echo # 離線模式（關鍵！）
echo OFFLINE_MODE=true
echo DISABLE_EXTERNAL_APIS=true
echo DISABLE_DATA_UPLOAD=true
echo HF_HUB_OFFLINE=true
echo TRANSFORMERS_OFFLINE=1
) > %PACKAGE_DIR%\config\.env.template

echo [5/6] 複製部署腳本...
copy scripts\install_models.bat %PACKAGE_DIR%\scripts\ 2>nul
copy scripts\setup_environment.bat %PACKAGE_DIR%\scripts\ 2>nul
copy scripts\verify_deployment.bat %PACKAGE_DIR%\scripts\ 2>nul

echo [6/6] 創建部署文檔...
copy 離線部署指南_30台電腦.md %PACKAGE_DIR%\docs\ 2>nul
copy AGENT模型配置說明.md %PACKAGE_DIR%\docs\ 2>nul

REM 創建快速開始指南
(
echo # 快速部署指南
echo.
echo ## 步驟 1: 安裝 Ollama
echo 下載並安裝: https://ollama.com
echo.
echo ## 步驟 2: 安裝 Python
echo 需要 Python 3.10 或更高版本
echo.
echo ## 步驟 3: 運行部署腳本
echo cd scripts
echo install_models.bat
echo setup_environment.bat
echo verify_deployment.bat
echo.
echo ## 步驟 4: 啟動服務
echo cd ..\code
echo 本地启动.bat
) > %PACKAGE_DIR%\QUICK_START.md

echo.
echo ========================================
echo 部署包創建完成
echo ========================================
echo.
echo 部署包位置: %PACKAGE_DIR%
echo.
echo 下一步：
echo 1. 檢查部署包大小和內容
echo 2. 使用 USB/內網 分發到30台電腦
echo 3. 在每台電腦上運行 scripts\install_models.bat
echo.
echo 注意：確保所有數據保持在本地，不連接互聯網
echo.
pause

