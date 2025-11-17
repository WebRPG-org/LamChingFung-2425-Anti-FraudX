@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo 系統健康檢查工具
echo ========================================
echo.

set ERROR_COUNT=0
set WARNING_COUNT=0

REM ===== 檢查 1: Python =====
echo [1/10] 檢查 Python...
python --version >nul 2>&1
if %errorlevel% equ 0 (
    python --version
    echo ✅ Python 已安裝
) else (
    echo ❌ Python 未安裝
    set /a ERROR_COUNT+=1
)
echo.

REM ===== 檢查 2: Ollama =====
echo [2/10] 檢查 Ollama...
ollama --version >nul 2>&1
if %errorlevel% equ 0 (
    ollama --version
    echo ✅ Ollama 已安裝
) else (
    echo ❌ Ollama 未安裝
    echo    請訪問: https://ollama.com
    set /a ERROR_COUNT+=1
)
echo.

REM ===== 檢查 3: Ollama 服務 =====
echo [3/10] 檢查 Ollama 服務...
curl -s http://localhost:11434/api/tags >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Ollama 服務正在運行
) else (
    echo ⚠️  Ollama 服務未運行
    echo    啟動方式: ollama serve
    set /a WARNING_COUNT+=1
)
echo.

REM ===== 檢查 4: Gemma 3 4B =====
echo [4/10] 檢查 Gemma 3 4B 模型...
ollama list 2>nul | findstr "gemma3:4b" >nul
if %errorlevel% equ 0 (
    echo ✅ Gemma 3 4B 已安裝
) else (
    echo ⚠️  Gemma 3 4B 未安裝（系統默認模型）
    echo    下載方式: ollama pull gemma3:4b
    set /a WARNING_COUNT+=1
)
echo.

REM ===== 檢查 5: Python 依賴 =====
echo [5/10] 檢查 Python 依賴...
python -c "import fastapi, uvicorn, requests" >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ 核心依賴已安裝
) else (
    echo ⚠️  部分依賴未安裝
    echo    安裝方式: pip install -r backend\requirements.txt
    set /a WARNING_COUNT+=1
)
echo.

REM ===== 檢查 6: 目錄結構 =====
echo [6/10] 檢查目錄結構...
set MISSING_DIRS=0
if not exist "backend\training_data\finetuning" (
    echo ⚠️  缺少: backend\training_data\finetuning
    set /a MISSING_DIRS+=1
)
if not exist "backend\models\finetuned" (
    echo ⚠️  缺少: backend\models\finetuned
    set /a MISSING_DIRS+=1
)
if not exist "backend\test_cases" (
    echo ⚠️  缺少: backend\test_cases
    set /a MISSING_DIRS+=1
)
if not exist "backend\evaluation_results" (
    echo ⚠️  缺少: backend\evaluation_results
    set /a MISSING_DIRS+=1
)

if !MISSING_DIRS! equ 0 (
    echo ✅ 所有必需目錄存在
) else (
    echo ⚠️  有 !MISSING_DIRS! 個目錄缺失（將自動創建）
    set /a WARNING_COUNT+=1
)
echo.

REM ===== 檢查 7: GPU 狀態 =====
echo [7/10] 檢查 GPU 狀態...
nvidia-smi --query-gpu=name --format=csv,noheader >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ GPU 可用:
    nvidia-smi --query-gpu=name --format=csv,noheader
) else (
    echo ℹ️  未檢測到 GPU（將使用 CPU 模式）
)
echo.

REM ===== 檢查 8: 訓練數據 =====
echo [8/10] 檢查訓練數據...
set TRAINING_FILES=0
for %%f in (backend\training_data\finetuning\*.jsonl) do set /a TRAINING_FILES+=1
if !TRAINING_FILES! gtr 0 (
    echo ✅ 發現 !TRAINING_FILES! 個訓練數據文件
) else (
    echo ℹ️  尚無訓練數據
    echo    運行模擬以生成訓練數據
)
echo.

REM ===== 檢查 9: Fine-Tuned 模型 =====
echo [9/10] 檢查 Fine-Tuned 模型...
set FINETUNED_COUNT=0
for /f "tokens=*" %%a in ('ollama list 2^>nul ^| findstr "anti-fraud"') do set /a FINETUNED_COUNT+=1
if !FINETUNED_COUNT! gtr 0 (
    echo ✅ 發現 !FINETUNED_COUNT! 個 Fine-Tuned 模型
    ollama list | findstr "anti-fraud"
) else (
    echo ℹ️  尚無 Fine-Tuned 模型
    echo    訓練方式: python backend\scripts\run_finetuning.py --model both
)
echo.

REM ===== 檢查 10: 核心文件 =====
echo [10/10] 檢查核心文件...
set MISSING_FILES=0
if not exist "backend\scripts\run_finetuning.py" (
    echo ❌ 缺少: run_finetuning.py
    set /a MISSING_FILES+=1
)
if not exist "backend\utils\finetuning_formatter.py" (
    echo ❌ 缺少: finetuning_formatter.py
    set /a MISSING_FILES+=1
)
if not exist "backend\api\simulation_routes.py" (
    echo ❌ 缺少: simulation_routes.py
    set /a MISSING_FILES+=1
)

if !MISSING_FILES! equ 0 (
    echo ✅ 所有核心文件存在
) else (
    echo ❌ 有 !MISSING_FILES! 個核心文件缺失
    set /a ERROR_COUNT+=1
)
echo.

REM ===== 總結 =====
echo ========================================
echo 檢查完成！
echo ========================================
echo.

if !ERROR_COUNT! equ 0 (
    if !WARNING_COUNT! equ 0 (
        echo ✅ 系統狀態：優秀
        echo    所有檢查都通過，系統已就緒！
    ) else (
        echo ⚠️  系統狀態：良好
        echo    發現 !WARNING_COUNT! 個警告，建議處理
    )
) else (
    echo ❌ 系統狀態：需要修復
    echo    發現 !ERROR_COUNT! 個錯誤，!WARNING_COUNT! 個警告
    echo    請根據上述提示修復問題
)

echo.
echo 快速修復命令:
echo   - 安裝 Python 依賴: pip install -r backend\requirements.txt
echo   - 下載 Gemma 3 4B: ollama pull gemma3:4b
echo   - 啟動 Ollama: ollama serve
echo   - 創建目錄: mkdir backend\training_data\finetuning
echo.

pause

