#!/bin/bash
# Anti‑Fraud Expert Model Deployment Script

echo "🚀 Starting deployment of the Anti‑Fraud Expert model..."

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "❌ Ollama is not installed. Please install Ollama first."
    exit 1
fi

# Check if base model exists
if ! ollama list | grep -q "gemma3:4b"; then
    echo "📥 Downloading base model gemma3:4b..."
    ollama pull gemma3:4b
fi

# Create the anti‑fraud expert model
echo "🔧 Creating anti‑fraud expert model..."
ollama create anti-fraud-expert -f Modelfile

# Test the model
echo "🧪 Testing the model..."
ollama run anti-fraud-expert "Hello, I am an anti‑fraud expert. How can I help you?"

echo "✅ Model deployment complete!"
echo "Usage: ollama run anti-fraud-expert"
