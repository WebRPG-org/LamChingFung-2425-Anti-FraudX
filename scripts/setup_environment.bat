@echo off
setlocal enabledelayedexpansion
chcp 65001 > nul

echo ========================================
echo 環境配置腳本
echo ========================================
echo.

REM 獲取腳本所在目錄
set SCRIPT_DIR=%~dp0
set PROJECT_DIR=%SCRIPT_DIR%..\code

if not exist "%PROJECT_DIR%" (
    echo [錯誤] 項目目錄不存在: %PROJECT_DIR%
    echo     請確保部署包結構正確
    pause
    exit /b 1
)

cd /d "%PROJECT_DIR%"
echo 項目目錄: %CD%

echo.
echo [步驟 1/5] 檢查 Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [錯誤] Python 未安裝或不在 PATH 中
    echo     請安裝 Python 3.10 或更高版本
    pause
    exit /b 1
)
python --version
echo [OK] Python 已安裝

echo.
echo [步驟 2/5] 安裝項目依賴...
if exist backend\requirements.txt (
    echo     正在安裝依賴（這可能需要幾分鐘）...
    pip install -r backend\requirements.txt
    if !errorlevel! equ 0 (
        echo     [OK] 依賴安裝成功
    ) else (
        echo     [警告] 部分依賴可能安裝失敗
        echo     請檢查錯誤信息
    )
) else (
    echo     [錯誤] requirements.txt 不存在
)

echo.
echo [步驟 3/5] 創建配置文件...
if not exist backend\.env (
    if exist ..\config\.env.template (
        copy ..\config\.env.template backend\.env
        echo     [OK] 配置文件已創建: backend\.env
        echo.
        echo     配置文件內容:
        type backend\.env
    ) else (
        echo     [警告] 配置模板不存在，創建默認配置...
        (
        echo AGENT_MODEL_EXPERT=anti-fraud-expert-20251111_220455
        echo AGENT_MODEL_SCAMMER=anti-fraud-scammer-20251111_220455
        echo AGENT_MODEL=gemma3:4b
        echo OLLAMA_BASE_URL=http://127.0.0.1:11434
        echo OFFLINE_MODE=true
        ) > backend\.env
        echo     [OK] 默認配置文件已創建
    )
) else (
    echo     [INFO] 配置文件已存在: backend\.env
    echo     如需更新，請手動編輯
)

echo.
echo [步驟 4/5] 創建數據目錄...
mkdir backend\training_data\finetuning 2>nul
mkdir backend\models\finetuned 2>nul
mkdir backend\db 2>nul
mkdir backend\db\chroma_db 2>nul
echo     [OK] 數據目錄已創建

echo.
echo [步驟 5/5] 驗證配置...
if exist backend\.env (
    echo     [OK] 配置文件存在
    echo.
    echo     當前配置:
    type backend\.env | findstr /V "^#" | findstr /V "^$"
) else (
    echo     [錯誤] 配置文件不存在
)

echo.
echo ========================================
echo 環境配置完成
echo ========================================
echo.
echo 項目目錄: %CD%
echo 配置文件: %CD%\backend\.env
echo.
echo 下一步：
echo 1. 檢查配置文件內容（backend\.env）
echo 2. 運行 verify_deployment.bat 驗證部署
echo 3. 運行 本地启动.bat 啟動服務
echo.
pause

