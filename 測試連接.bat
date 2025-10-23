@echo off
chcp 65001 >nul
echo ========================================
echo 測試 AI-Agent 系統連接
echo ========================================
echo.

echo [1/3] 測試 http://127.0.0.1:8000 ...
curl -s http://127.0.0.1:8000 >nul 2>&1
if errorlevel 1 (
    echo ❌ 127.0.0.1:8000 無法連接
    echo.
    goto check_localhost
) else (
    echo ✅ 127.0.0.1:8000 連接成功
)

:check_localhost
echo.
echo [2/3] 測試 http://localhost:8000 ...
curl -s http://localhost:8000 >nul 2>&1
if errorlevel 1 (
    echo ❌ localhost:8000 無法連接
    echo.
) else (
    echo ✅ localhost:8000 連接成功
)

echo.
echo [3/3] 檢查端口占用...
netstat -ano | findstr :8000
if errorlevel 1 (
    echo ⚠️  端口 8000 未被占用
    echo 提示：系統可能未啟動
) else (
    echo ✅ 端口 8000 正在使用中
)

echo.
echo ========================================
echo 測試完成
echo ========================================
echo.

echo 如果連接失敗，請：
echo 1. 停止當前服務 (Ctrl+C)
echo 2. 執行: python start_server.py
echo 3. 確保看到: http://127.0.0.1:8000
echo.

pause


