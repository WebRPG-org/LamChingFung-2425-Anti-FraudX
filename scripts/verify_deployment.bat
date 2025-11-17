@echo off
setlocal enabledelayedexpansion
chcp 65001 > nul

echo ========================================
echo 部署驗證腳本
echo ========================================
echo.

set ERROR_COUNT=0
set WARNING_COUNT=0

echo [檢查 1/6] Ollama 服務...
curl -s http://localhost:11434/api/tags >nul 2>&1
if %errorlevel% equ 0 (
    echo     [OK] Ollama 服務運行中
) else (
    echo     [錯誤] Ollama 服務未運行
    echo         請運行: ollama serve
    set /a ERROR_COUNT+=1
)

echo.
echo [檢查 2/6] 模型安裝...
ollama list | findstr "anti-fraud" >nul 2>&1
if %errorlevel% equ 0 (
    echo     [OK] Fine-Tuned 模型已安裝
    echo.
    echo     已安裝的模型:
    ollama list | findstr "anti-fraud"
) else (
    echo     [錯誤] Fine-Tuned 模型未找到
    echo         請運行: scripts\install_models.bat
    set /a ERROR_COUNT+=1
)

echo.
echo [檢查 3/6] Python 環境...
python --version >nul 2>&1
if %errorlevel% equ 0 (
    python --version
    echo     [OK] Python 已安裝
) else (
    echo     [錯誤] Python 未安裝
    set /a ERROR_COUNT+=1
)

echo.
echo [檢查 4/6] 項目依賴...
python -c "import fastapi" 2>nul
if %errorlevel% equ 0 (
    echo     [OK] FastAPI 已安裝
) else (
    echo     [錯誤] FastAPI 未安裝
    set /a ERROR_COUNT+=1
)

python -c "import transformers" 2>nul
if %errorlevel% equ 0 (
    echo     [OK] Transformers 已安裝
) else (
    echo     [警告] Transformers 未安裝（Fine-Tuning 需要）
    set /a WARNING_COUNT+=1
)

echo.
echo [檢查 5/6] 配置文件...
if exist backend\.env (
    echo     [OK] 配置文件存在
    echo.
    echo     關鍵配置:
    type backend\.env | findstr "AGENT_MODEL" | findstr /V "^#"
    type backend\.env | findstr "OLLAMA_BASE_URL" | findstr /V "^#"
    type backend\.env | findstr "OFFLINE_MODE" | findstr /V "^#"
    
    REM 檢查是否配置為本地
    type backend\.env | findstr "127.0.0.1" >nul 2>&1
    if %errorlevel% equ 0 (
        echo     [OK] Ollama 配置為本地模式（數據安全）
    ) else (
        echo     [警告] Ollama URL 可能不是本地地址
        set /a WARNING_COUNT+=1
    )
) else (
    echo     [錯誤] 配置文件不存在
    echo         請運行: scripts\setup_environment.bat
    set /a ERROR_COUNT+=1
)

echo.
echo [檢查 6/6] 數據目錄...
if exist backend\training_data (
    echo     [OK] 訓練數據目錄存在
) else (
    echo     [警告] 訓練數據目錄不存在（將自動創建）
    set /a WARNING_COUNT+=1
)

if exist backend\models (
    echo     [OK] 模型目錄存在
) else (
    echo     [警告] 模型目錄不存在（將自動創建）
    set /a WARNING_COUNT+=1
)

echo.
echo ========================================
echo 驗證結果
echo ========================================
echo.
if %ERROR_COUNT% equ 0 (
    if %WARNING_COUNT% equ 0 (
        echo [SUCCESS] 所有檢查通過！部署成功！
    ) else (
        echo [SUCCESS] 核心檢查通過，有 %WARNING_COUNT% 個警告
    )
) else (
    echo [FAILED] 發現 %ERROR_COUNT% 個錯誤，%WARNING_COUNT% 個警告
    echo     請修復錯誤後重新驗證
)

echo.
echo 電腦名稱: %COMPUTERNAME%
echo 驗證時間: %date% %time%
echo.
pause

