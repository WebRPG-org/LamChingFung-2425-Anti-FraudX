@echo off
chcp 65001 >nul
echo ========================================
echo 安裝 AI-Agent 依賴
echo ========================================
echo.

cd backend

echo 正在安裝依賴，這可能需要幾分鐘...
echo.

pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo ========================================
    echo ⚠️  完整依賴安裝失敗
    echo ========================================
    echo.
    echo 嘗試安裝核心依賴...
    echo.
    
    pip install fastapi uvicorn requests python-dotenv python-multipart ollama chromadb
    
    if errorlevel 1 (
        echo.
        echo 核心依賴安裝也失敗
        echo 請檢查網絡連接和 pip 配置
        pause
        exit /b 1
    )
    
    echo.
    echo ========================================
    echo ✅ 核心依賴安裝完成
    echo ========================================
    echo.
    echo 注意：某些功能可能不可用
    echo 但 RPG Maker 功能應該可以正常使用
    echo.
) else (
    echo.
    echo ========================================
    echo ✅ 所有依賴安裝完成
    echo ========================================
    echo.
)

pause

