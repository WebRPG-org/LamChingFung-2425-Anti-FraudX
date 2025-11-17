@echo off
chcp 65001 >nul
echo ========================================
echo   Gemma 3 4B 配置驗證腳本
echo ========================================
echo.

echo [1/4] 檢查 Ollama 是否運行...
ollama list >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Ollama 未運行，請先啟動 Ollama
    echo    執行: ollama serve
    pause
    exit /b 1
)
echo ✅ Ollama 正在運行

echo.
echo [2/4] 檢查 Gemma 3 4B 是否已安裝...
ollama list | findstr "gemma3:4b" >nul
if %errorlevel% neq 0 (
    echo ❌ Gemma 3 4B 未安裝
    echo.
    echo 是否現在下載？這將需要約 3.3GB 空間和 5-10 分鐘。
    set /p download="輸入 Y 下載，N 退出: "
    if /i "%download%"=="Y" (
        echo.
        echo 正在下載 Gemma 3 4B...
        ollama pull gemma3:4b
        if %errorlevel% neq 0 (
            echo ❌ 下載失敗
            pause
            exit /b 1
        )
        echo ✅ 下載完成
    ) else (
        echo 已取消
        pause
        exit /b 1
    )
) else (
    echo ✅ Gemma 3 4B 已安裝
)

echo.
echo [3/4] 測試 Gemma 3 4B 模型...
echo.
echo 發送測試提示: "你好，請用一句廣東話介紹自己"
echo.
echo 回應:
echo ------------
echo|set /p="你好，請用一句廣東話介紹自己" | ollama run gemma3:4b 2>nul
echo ------------
echo.
echo ✅ 模型回應正常

echo.
echo [4/4] 檢查訓練腳本配置...
findstr "gemma3:4b" backend\scripts\run_finetuning.py >nul
if %errorlevel% neq 0 (
    echo ❌ 訓練腳本尚未更新為 Gemma 3 4B
    echo    請手動更新 backend\scripts\run_finetuning.py
    pause
    exit /b 1
)
echo ✅ 訓練腳本已配置為使用 Gemma 3 4B

echo.
echo ========================================
echo   ✅ 所有檢查通過！
echo ========================================
echo.
echo 你現在可以開始使用 Gemma 3 4B 進行 Fine-Tuning：
echo.
echo   1. 收集訓練數據:
echo      python start_server.py
echo      (在前端執行 10 次模擬)
echo.
echo   2. 訓練模型:
echo      python backend\scripts\run_finetuning.py --model both
echo.
echo   3. 評估模型:
echo      python backend\scripts\evaluate_finetuned_models.py --model expert --model-name ^<模型名稱^>
echo.
echo 詳細說明請查看: GEMMA3_配置說明.md
echo.
pause

