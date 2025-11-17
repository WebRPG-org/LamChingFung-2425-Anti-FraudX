#!/bin/bash

echo "🌐 Codespace 後端連接測試"
echo "================================"
echo ""

# Codespace URL
CODESPACE_URL="https://crispy-space-goggles-r4rjqj6vpvr5fggq-8000.app.github.dev"

echo "📍 測試 URL: $CODESPACE_URL"
echo ""

# 測試 1: 健康檢查
echo "✅ 測試 1: 後端健康檢查"
curl -s "$CODESPACE_URL" | jq '.' 2>/dev/null || curl -s "$CODESPACE_URL"
echo ""
echo ""

# 測試 2: Chat API 健康檢查
echo "✅ 測試 2: Chat API 健康檢查"
curl -s "$CODESPACE_URL/chat/health" | jq '.' 2>/dev/null || curl -s "$CODESPACE_URL/chat/health"
echo ""
echo ""

# 測試 3: 遊戲 API 健康檢查
echo "✅ 測試 3: 遊戲 API 健康檢查"
curl -s "$CODESPACE_URL/api/game/health" | jq '.' 2>/dev/null || curl -s "$CODESPACE_URL/api/game/health"
echo ""
echo ""

# 測試 4: 發送測試消息到 AI
echo "✅ 測試 4: 發送測試消息到 AI"
curl -X POST "$CODESPACE_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "role": "友善的測試助手",
    "message": "你好，這是一個測試",
    "history": []
  }' \
  -s | jq '.' 2>/dev/null || curl -X POST "$CODESPACE_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{"role":"友善的測試助手","message":"你好，這是一個測試","history":[]}' \
  -s
echo ""
echo ""

# 測試 5: 啟動遊戲會話
echo "✅ 測試 5: 啟動遊戲會話"
curl -X POST "$CODESPACE_URL/api/game/start" \
  -H "Content-Type: application/json" \
  -d '{"persona_type": "A"}' \
  -s | jq '.' 2>/dev/null || curl -X POST "$CODESPACE_URL/api/game/start" \
  -H "Content-Type: application/json" \
  -d '{"persona_type":"A"}' \
  -s
echo ""
echo ""

echo "================================"
echo "測試完成！"
echo ""
echo "📝 如果所有測試都返回正確的 JSON 回應，表示配置成功！"
echo ""
echo "🎮 下一步："
echo "1. 將 RPG_platform/RPG_Project 文件夾複製到本地電腦"
echo "2. 在本地運行: python -m http.server 8080"
echo "3. 在瀏覽器打開: http://localhost:8080"
echo "4. 開始測試遊戲！"
echo ""
