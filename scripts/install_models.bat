@echo off
setlocal enabledelayedexpansion
chcp 65001 > nul

echo ========================================
echo 離線模型安裝腳本
echo ========================================
echo.
echo 此腳本將導入 Fine-Tuned 模型到本地 Ollama
echo 所有模型將完全離線運行，數據不會流出
echo.

REM 檢查 Ollama 是否安裝
where ollama >nul 2>&1
if %errorlevel% neq 0 (
    echo [錯誤] Ollama 未安裝
    echo.
    echo 請先安裝 Ollama:
    echo 1. 訪問 https://ollama.com
    echo 2. 下載並安裝 Ollama
    echo 3. 重新運行此腳本
    echo.
    pause
    exit /b 1
)

echo [檢查] Ollama 已安裝
ollama --version

echo.
echo [步驟 1/4] 啟動 Ollama 服務...
taskkill /F /IM "ollama.exe" /T >nul 2>&1
timeout /t 2 /nobreak >nul

start /B ollama serve
echo     等待 Ollama 啟動...
timeout /t 5 /nobreak >nul

REM 檢查 Ollama 是否運行
curl -s http://localhost:11434/api/tags >nul 2>&1
if %errorlevel% neq 0 (
    echo [錯誤] Ollama 服務啟動失敗
    echo     請手動運行: ollama serve
    pause
    exit /b 1
)
echo [OK] Ollama 服務運行中

echo.
echo [步驟 2/4] 導入基礎模型...
if exist models\gemma3_4b_base.tar (
    echo     導入 gemma3:4b...
    ollama load models\gemma3_4b_base.tar
    if !errorlevel! equ 0 (
        echo     [OK] 基礎模型導入成功
    ) else (
        echo     [警告] 基礎模型可能已存在
    )
) else (
    echo     [跳過] 基礎模型文件不存在
    echo     提示: 可以手動下載: ollama pull gemma3:4b
)

echo.
echo [步驟 3/4] 導入 Fine-Tuned 模型...
if exist models\expert_model.tar (
    echo     導入專家模型: anti-fraud-expert-20251111_220455...
    ollama load models\expert_model.tar
    if !errorlevel! equ 0 (
        echo     [OK] 專家模型導入成功
    ) else (
        echo     [錯誤] 專家模型導入失敗
    )
) else (
    echo     [錯誤] 專家模型文件不存在: models\expert_model.tar
)

if exist models\scammer_model.tar (
    echo     導入騙徒模型: anti-fraud-scammer-20251111_220455...
    ollama load models\scammer_model.tar
    if !errorlevel! equ 0 (
        echo     [OK] 騙徒模型導入成功
    ) else (
        echo     [錯誤] 騙徒模型導入失敗
    )
) else (
    echo     [錯誤] 騙徒模型文件不存在: models\scammer_model.tar
)

echo.
echo [步驟 4/4] 驗證模型安裝...
echo.
echo 已安裝的模型列表:
ollama list
echo.

REM 檢查 Fine-Tuned 模型
ollama list | findstr "anti-fraud" >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Fine-Tuned 模型已成功安裝
    echo.
    echo 可用的模型:
    ollama list | findstr "anti-fraud"
) else (
    echo [警告] Fine-Tuned 模型未找到
    echo     請檢查模型文件是否存在
)

echo.
echo ========================================
echo 模型安裝完成
echo ========================================
echo.
echo 下一步：
echo 1. 運行 setup_environment.bat 配置環境
echo 2. 運行 verify_deployment.bat 驗證部署
echo.
pause

