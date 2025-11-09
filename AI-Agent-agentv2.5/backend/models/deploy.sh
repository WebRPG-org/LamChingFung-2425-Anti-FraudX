echo "🚀 開始部署 AI 反詐騙專家模型..."

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "❌ Ollama 未安裝，請先安裝 Ollama"
    exit 1
fi

# Check if the base model exists
if ! ollama list | grep -q "gemma3:4b"; then
    echo "📥 下載基礎模型 gemma3:4b..."
    ollama pull gemma3:4b
fi

# Create the anti-fraud expert model
echo "🔧 創建防騙專家模型..."
ollama create anti-fraud-expert -f Modelfile

# Test the model
echo "🧪 測試模型..."
ollama run anti-fraud-expert "你好，我是防騙專家，有什麼可以幫助你的嗎？"

echo "✅ 模型部署完成！"
echo "使用方法: ollama run anti-fraud-expert"
