#!/bin/bash

# AI-Agent 快速啟動腳本
echo "🚀 啟動 AI-Agent 系統..."

# 檢查 Docker 是否安裝
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安裝，請先安裝 Docker"
    exit 1
fi

# 檢查 Docker Compose 是否安裝
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose 未安裝，請先安裝 Docker Compose"
    exit 1
fi

# 檢查環境文件
if [ ! -f "backend/.env" ]; then
    echo "📝 創建環境配置文件..."
    cp env.example backend/.env
    echo "⚠️  請編輯 backend/.env 文件，添加你的 API 密鑰"
fi

# 啟動服務
echo "🐳 啟動 Docker 容器..."
docker-compose up --build -d

# 等待服務啟動
echo "⏳ 等待服務啟動..."
sleep 10

# 檢查服務狀態
echo "🔍 檢查服務狀態..."
docker-compose ps

# 運行健康檢查
echo "🏥 運行健康檢查..."
python test_system.py

echo ""
echo "🎉 AI-Agent 系統已啟動！"
echo ""
echo "📱 前端: http://localhost:5173"
echo "🔧 後端: http://localhost:8000"
echo "📊 API 文檔: http://localhost:8000/docs"
echo ""
echo "📋 可用功能:"
echo "  - 文字分析"
echo "  - 螢幕錄影"
echo "  - 長者模式"
echo "  - 多媒體處理"
echo "  - CrewAI 深度分析"
echo ""
echo "🛑 停止服務: docker-compose down"
echo "📝 查看日誌: docker-compose logs"

