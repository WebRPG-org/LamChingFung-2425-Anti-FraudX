@echo off
chcp 65001 >nul
echo ========================================
echo   測試腳本編碼
echo ========================================
echo.

echo 測試中文字符:
echo    - 所有服務在背景運行 (最小化窗口)
echo    - 關閉此窗口不影響服務運行
echo.

echo 測試特殊符號:
echo    - 命中率 30-50%%
echo    - 響應時間 小於50ms
echo    - 平均響應 小於200ms
echo.

echo 測試完成!
echo.
pause
