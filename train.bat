@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

set ROOT_DIR=%~dp0
set VENV_PYTHON=%ROOT_DIR%venv\Scripts\python.exe
set BACKEND_DIR=%ROOT_DIR%backend

echo ================================================================================
echo  AI 防詐騙訓練系統 - 一站式訓練腳本
echo ================================================================================
echo.

:MENU
echo 請選擇操作:
echo   [1] 完整流程 (爬蟲 → 訓練模擬 → Fine-tune → 生成模型)
echo   [2] 僅執行爬蟲抓取
echo   [3] 僅執行訓練模擬
echo   [4] 僅執行 Fine-tune 數據生成
echo   [5] 僅生成 Ollama 模型
echo   [6] 開啟工具中心 (http://localhost:8000/tools)
echo   [Q] 退出
echo.
set /p CHOICE=請輸入選項: 

if /i "%CHOICE%"=="1" goto FULL
if /i "%CHOICE%"=="2" goto SCRAPER
if /i "%CHOICE%"=="3" goto TRAINING
if /i "%CHOICE%"=="4" goto FINETUNE
if /i "%CHOICE%"=="5" goto MODELGEN
if /i "%CHOICE%"=="6" goto OPEN_TOOLS
if /i "%CHOICE%"=="Q" goto END
goto MENU

:FULL
echo.
echo [INFO] 開始完整訓練流程...
echo.

echo [1/4] 執行爬蟲抓取...
call :RUN_SCRAPER
if errorlevel 1 echo [WARNING] 爬蟲執行失敗，繼續下一步
echo.

echo [2/4] 執行訓練模擬...
set /p ROUNDS=請輸入訓練輪數 (預設 3): 
if "%ROUNDS%"=="" set ROUNDS=3
call :RUN_TRAINING
if errorlevel 1 echo [WARNING] 訓練模擬執行失敗，繼續下一步
echo.

echo [3/4] 執行 Fine-tune 數據生成...
call :RUN_FINETUNE
if errorlevel 1 echo [WARNING] Fine-tune 執行失敗，繼續下一步
echo.

echo [4/4] 生成 Ollama 模型...
call :RUN_MODELGEN
if errorlevel 1 echo [WARNING] 模型生成執行失敗
echo.

echo ================================================================================
echo  完整流程完成！
echo  訓練記錄: %BACKEND_DIR%\training_data\
echo  模型檔案: %BACKEND_DIR%\models\
echo  工具中心: http://localhost:8000/tools
echo ================================================================================
goto END

:SCRAPER
echo.
call :RUN_SCRAPER
goto END

:TRAINING
echo.
set /p ROUNDS=請輸入訓練輪數 (預設 3): 
if "%ROUNDS%"=="" set ROUNDS=3
call :RUN_TRAINING
goto END

:FINETUNE
echo.
call :RUN_FINETUNE
goto END

:MODELGEN
echo.
call :RUN_MODELGEN
goto END

:OPEN_TOOLS
start http://localhost:8000/tools
goto END

:: ── 子程序 ──────────────────────────────────────────

:RUN_SCRAPER
echo [執行] 爬蟲抓取 ADCC 詐騙警示...
"%VENV_PYTHON%" "%BACKEND_DIR%\scripts\scraper.py"
if errorlevel 1 (
    echo [ERROR] 爬蟲執行失敗 (exit code: %errorlevel%)
    exit /b 1
)
echo [OK] 爬蟲完成
exit /b 0

:RUN_TRAINING
echo [執行] AI 三方對話訓練模擬 (%ROUNDS% 輪)...
set TRAINING_ROUNDS=%ROUNDS%
"%VENV_PYTHON%" "%BACKEND_DIR%\scripts\training_runner.py"
if errorlevel 1 (
    echo [ERROR] 訓練模擬執行失敗 (exit code: %errorlevel%)
    exit /b 1
)
echo [OK] 訓練模擬完成
exit /b 0

:RUN_FINETUNE
echo [執行] Fine-tune 數據生成...
"%VENV_PYTHON%" "%BACKEND_DIR%\scripts\generate_finetuning_data.py"
if errorlevel 1 (
    echo [ERROR] Fine-tune 執行失敗 (exit code: %errorlevel%)
    exit /b 1
)
echo [OK] Fine-tune 完成
exit /b 0

:RUN_MODELGEN
echo [執行] 生成 Ollama Modelfile...
"%VENV_PYTHON%" "%BACKEND_DIR%\scripts\model_fine_tuning.py"
if errorlevel 1 (
    echo [ERROR] 模型生成失敗 (exit code: %errorlevel%)
    exit /b 1
)
echo [OK] Modelfile 生成完成

echo.
echo [執行] ollama create anti-fraud-expert...
ollama create anti-fraud-expert -f "%BACKEND_DIR%\models\Modelfile"
if errorlevel 1 (
    echo [WARNING] ollama create 失敗，請確認 Ollama 已安裝並運行
    echo [INFO] 手動執行: ollama create anti-fraud-expert -f backend\models\Modelfile
    exit /b 1
)
echo [OK] 模型 anti-fraud-expert 已建立
exit /b 0

:END
echo.
pause
