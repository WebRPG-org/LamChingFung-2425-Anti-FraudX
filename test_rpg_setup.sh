#!/bin/bash

echo "=========================================="
echo "🧪 AI-Agent RPG Maker 整合測試"
echo "=========================================="
echo ""

# 顏色定義
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 測試 1: 檢查後端服務
echo "📡 測試 1: 檢查後端服務..."
response=$(curl -s http://localhost:8000)
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ 後端服務運行中${NC}"
    echo "   回應: $response"
else
    echo -e "${RED}❌ 後端服務未運行${NC}"
    echo "   請執行: python start_server.py"
    exit 1
fi
echo ""

# 測試 2: 檢查 Ollama 服務
echo "🤖 測試 2: 檢查 Ollama 服務..."
ollama_response=$(curl -s http://localhost:11434/api/tags)
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Ollama 服務運行中${NC}"
    echo "   已安裝的模型:"
    echo "$ollama_response" | grep -o '"name":"[^"]*"' | cut -d'"' -f4
else
    echo -e "${RED}❌ Ollama 服務未運行${NC}"
    echo "   請確保 Ollama 已啟動"
fi
echo ""

# 測試 3: 測試聊天 API
echo "💬 測試 3: 測試聊天 API..."
chat_response=$(curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "role": "友善的測試助手",
    "message": "請用一句話介紹你自己",
    "history": []
  }')

if echo "$chat_response" | grep -q "reply"; then
    echo -e "${GREEN}✅ 聊天 API 正常${NC}"
    echo "   AI 回應: $(echo $chat_response | grep -o '"reply":"[^"]*"' | cut -d'"' -f4)"
else
    echo -e "${RED}❌ 聊天 API 異常${NC}"
    echo "   回應: $chat_response"
fi
echo ""

# 測試 4: 測試遊戲啟動 API
echo "🎮 測試 4: 測試遊戲啟動 API..."
game_response=$(curl -s -X POST http://localhost:8000/api/game/start \
  -H "Content-Type: application/json" \
  -d '{"persona_type": "A"}')

if echo "$game_response" | grep -q "session_id"; then
    echo -e "${GREEN}✅ 遊戲啟動 API 正常${NC}"
    session_id=$(echo $game_response | grep -o '"session_id":"[^"]*"' | cut -d'"' -f4)
    echo "   會話ID: $session_id"
    
    # 測試 5: 測試結束遊戲
    echo ""
    echo "🏁 測試 5: 測試結束遊戲 API..."
    end_response=$(curl -s -X POST "http://localhost:8000/api/game/end?session_id=$session_id")
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ 結束遊戲 API 正常${NC}"
    else
        echo -e "${YELLOW}⚠️  結束遊戲 API 可能有問題${NC}"
    fi
else
    echo -e "${RED}❌ 遊戲啟動 API 異常${NC}"
    echo "   回應: $game_response"
fi
echo ""

# 測試 6: 檢查插件文件
echo "📦 測試 6: 檢查 RPG Maker 插件..."
plugin_dir="/workspaces/fyp2526-MakHiuFung-2425/RPG_platform/RPG_Project/js/plugins"

if [ -f "$plugin_dir/AI_Bridge.js" ]; then
    echo -e "${GREEN}✅ AI_Bridge.js 已安裝${NC}"
else
    echo -e "${RED}❌ AI_Bridge.js 未找到${NC}"
fi

if [ -f "$plugin_dir/AntiFraudGame.js" ]; then
    echo -e "${GREEN}✅ AntiFraudGame.js 已安裝${NC}"
else
    echo -e "${RED}❌ AntiFraudGame.js 未找到${NC}"
fi
echo ""

# 總結
echo "=========================================="
echo "✨ 測試完成！"
echo "=========================================="
echo ""
echo "📝 下一步:"
echo "1. 打開 RPG Maker MV"
echo "2. 打開項目: RPG_platform/RPG_Project/"
echo "3. 工具 → 插件管理器，啟用兩個插件"
echo "4. 創建測試事件（參考 RPG_MV_快速測試.md）"
echo "5. 按 Ctrl+R 測試遊戲"
echo ""
echo "📚 文檔:"
echo "- API 文檔: http://localhost:8000/docs"
echo "- 測試指南: RPG_MV_快速測試.md"
echo "- 整合指南: RPG_MAKER_整合指南.md"
echo ""
