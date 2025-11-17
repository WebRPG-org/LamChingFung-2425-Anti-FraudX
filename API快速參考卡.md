# API 快速參考卡

## 🎯 `/api/chat` - 簡單聊天端點

### 基本信息
- **用途**: RPG Maker、前端、外部集成
- **文件**: `backend/api/chat_routes.py`
- **模型**: 從環境變量 `AGENT_MODEL` (默認 `gemma3:4b`)

### 快速使用
```python
import requests

response = requests.post("http://localhost:8000/chat", json={
    "role": "你是一個友善的助手",
    "message": "你好",
    "history": []
})

print(response.json()["reply"])
```

### 特點
✅ 簡單易用  
✅ 支持對話歷史  
✅ 自動繁體中文  
❌ 無重試邏輯  
❌ 參數控制有限  

---

## ⚙️ `/api/generate` - 高級LLM端點

### 基本信息
- **用途**: Agent 系統、Fine-Tuning
- **文件**: `backend/llms/ollama_llm.py`
- **模型**: 實例化時指定

### 快速使用
```python
from llms.ollama_llm import OllamaLlm

llm = OllamaLlm(model="gemma3:4b")
response = await llm.generate_content_async(llm_request)
```

### 特點
✅ 完整參數控制  
✅ 自動重試 (3次)  
✅ 異步支持  
✅ 自動模型下載  
❌ 使用較複雜  

---

## 📊 快速決策

| 你的場景 | 使用 |
|---------|------|
| 🎮 RPG Maker 插件 | `/api/chat` |
| 🌐 簡單前端聊天 | `/api/chat` |
| 🤖 Agent 系統 | `/api/generate` |
| 🎯 反詐騙模擬 | `/api/generate` |
| 🔬 Fine-Tuning | `/api/generate` |
| 📱 快速原型 | `/api/chat` |

---

## 🔧 配置

### `/api/chat` 環境變量
```bash
AGENT_MODEL=gemma3:4b
```

### `/api/generate` 環境變量
```bash
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_TEMPERATURE=0.5
OLLAMA_TOP_P=0.85
OLLAMA_NUM_CTX=4096
OLLAMA_AUTO_PULL=1
```

---

**詳細文檔**: `API端點分析_Chat與Generate.md`

