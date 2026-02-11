@echo off
chcp 65001 > nul
echo ================================================================================
echo 測試 RPGv2 與 Backend Agent 連接
echo ================================================================================
echo.

echo [1/5] 測試 Backend 健康狀態...
curl -s http://localhost:8000/health
echo.
echo.

echo [2/5] 測試 Game V2 API...
curl -s http://localhost:8000/api/game/v2/health
echo.
echo.

echo [3/5] 測試 RPGv2 Battle API...
curl -s http://localhost:8000/api/rpgv2/battle/health
echo.
echo.

echo [4/5] 測試騙案類型列表...
curl -s http://localhost:8000/api/game/v2/scam-types
echo.
echo.

echo [5/5] 測試 RPGv2 遊戲模式列表...
curl -s http://localhost:8000/api/rpgv2/game/modes
echo.
echo.

echo ================================================================================
echo 測試完成！
echo ================================================================================
echo.
echo 如果所有 API 都返回 JSON 數據，表示連接正常。
echo.
pause

