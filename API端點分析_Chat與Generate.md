# API 端點分析：/api/chat vs /api/generate

**分析日期**: 2024-11-11  
**系統版本**: v2.1

---

## 📋 概述

系統中有兩個主要的 AI 對話端點：
1. **`/api/chat`** - FastAPI 路由，用於簡單的聊天交互（RPG Maker、前端等）
2. **`/api/generate`** - Ollama 原生端點，用於底層 LLM 調用

---

## 🔍 詳細分析

### 1. `/api/chat` 端點

**位置**: `backend/api/chat_routes.py`

#### 架構圖

```
客戶端（RPG Maker / 前端）
    ↓
FastAPI: /api/chat
    ↓
call_ollama() 函數
    ↓
requests.post(OLLAMA_API_URL)
    ↓
Ollama: /api/chat
    ↓
Gemma 3 4B 模型
    ↓
返回響應
```

#### 端點詳情

##### 1.1 主要端點

**路徑**: `POST /chat`

**請求格式**:
```json
{
  "role": "你是一個友善的助手",
  "message": "你好，請介紹自己",
  "history": [
    {
      "role": "user",
      "content": "之前的問題"
    },
    {
      "role": "assistant",
      "content": "之前的回答"
    }
  ]
}
```

**響應格式**:
```json
{
  "reply": "你好！我是一個...",
  "success": true
}
```

##### 1.2 替代端點（向後兼容）

**路徑**: `POST /api/chat/send`

功能與 `/chat` 完全相同，用於向後兼容舊客戶端。

##### 1.3 健康檢查端點

**路徑**: `GET /chat/health`

**響應**:
```json
{
  "status": "ok",
  "ollama": "running"
}
```

#### 核心函數：`call_ollama()`

```python
async def call_ollama(role: str, message: str, history: List[Dict] = None) -> str:
    """調用 Ollama API"""
    # 1. 構建 system prompt
    system_prompt = f"{role}\n請用繁體中文回應。"
    
    # 2. 構建消息列表
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history)
    messages.append({"role": "user", "content": message})
    
    # 3. 獲取模型名稱（默認 gemma3:4b）
    model_name = os.getenv("AGENT_MODEL", "gemma3:4b")
    
    # 4. 構建 payload
    payload = {
        "model": model_name,
        "messages": messages,
        "stream": False
    }
    
    # 5. 調用 Ollama
    response = requests.post(OLLAMA_API_URL, json=payload, timeout=180)
    return result.get("message", {}).get("content", "")
```

#### 特點

| 特性 | 說明 |
|-----|------|
| **用途** | 簡單的聊天交互，適合外部客戶端 |
| **協議** | HTTP REST API |
| **格式** | JSON Request/Response |
| **歷史** | 支持對話歷史 |
| **超時** | 180 秒 |
| **重試** | 無（單次請求） |
| **模型** | 從環境變量讀取（默認 gemma3:4b） |
| **串流** | 不支持（stream=False） |

#### 使用場景

✅ **適合**:
- RPG Maker 插件對話
- 簡單的前端聊天
- 外部系統集成
- 快速原型開發

❌ **不適合**:
- 複雜的多輪對話（需要更多控制）
- 需要串流輸出
- 需要高級生成參數控制

---

### 2. `/api/generate` 端點

**位置**: Ollama 服務原生端點，被 `backend/llms/ollama_llm.py` 調用

#### 架構圖

```
內部系統（Agent、Simulation）
    ↓
OllamaLlm 類
    ↓
generate_content_async()
    ↓
httpx.AsyncClient.post("/api/generate")
    ↓
Ollama 服務: /api/generate
    ↓
Gemma 3 4B 模型
    ↓
返回響應
```

#### 端點詳情

**路徑**: `POST /api/generate` （Ollama 服務）

**請求格式**:
```json
{
  "model": "gemma3:4b",
  "prompt": "完整的提示文本",
  "system": "系統指令",
  "stream": false,
  "options": {
    "temperature": 0.5,
    "top_p": 0.85,
    "top_k": 40,
    "repeat_penalty": 1.1,
    "num_ctx": 4096,
    "num_predict": null
  }
}
```

**響應格式**:
```json
{
  "model": "gemma3:4b",
  "created_at": "2024-11-11T...",
  "response": "生成的文本回應",
  "done": true
}
```

#### 核心類：`OllamaLlm`

```python
class OllamaLlm(BaseLlm):
    async def generate_content_async(self, llm_request: LlmRequest, stream: bool = False):
        # 1. 提取文本和系統指令
        prompt = _extract_text_from_contents(llm_request.contents)
        system_text = llm_request.system_instruction
        
        # 2. 配置生成參數（可通過環境變量覆蓋）
        options = {
            "temperature": float(os.getenv("OLLAMA_TEMPERATURE", "0.5")),
            "top_p": float(os.getenv("OLLAMA_TOP_P", "0.85")),
            "repeat_penalty": float(os.getenv("OLLAMA_REPEAT_PENALTY", "1.1")),
            "num_ctx": int(os.getenv("OLLAMA_NUM_CTX", "4096")),
        }
        
        # 3. 構建 payload
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system_text,
            "stream": False,
            "options": options
        }
        
        # 4. 自動拉取模型（如果不存在）
        if os.getenv("OLLAMA_AUTO_PULL", "1") != "0":
            await client.post("/api/pull", json={"name": self.model})
        
        # 5. 重試邏輯（最多 3 次）
        for attempt in range(3):
            try:
                resp = await client.post("/api/generate", json=payload)
                data = resp.json()
                return data.get("response", "")
            except (httpx.ConnectError, httpx.TimeoutException) as e:
                if attempt < 2:
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # 指數退避
                else:
                    raise
```

#### 特點

| 特性 | 說明 |
|-----|------|
| **用途** | 底層 LLM 調用，用於 Agent 系統 |
| **協議** | HTTP POST（異步） |
| **格式** | Ollama 原生格式 |
| **歷史** | 需要在 prompt 中手動管理 |
| **超時** | 300 秒（可配置） |
| **重試** | 3 次，指數退避 |
| **模型** | 實例化時指定 |
| **串流** | 支持（可配置） |
| **參數控制** | 完整的生成參數（temperature, top_p等） |
| **自動拉取** | 支持（第一次使用自動下載模型） |

#### 環境變量配置

| 變量 | 默認值 | 說明 |
|-----|-------|------|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama 服務地址 |
| `OLLAMA_TEMPERATURE` | `0.5` | 溫度（0-1，越高越隨機） |
| `OLLAMA_TOP_P` | `0.85` | 核採樣閾值 |
| `OLLAMA_TOP_K` | `None` | 候選token數 |
| `OLLAMA_REPEAT_PENALTY` | `1.1` | 重複懲罰 |
| `OLLAMA_NUM_CTX` | `4096` | 上下文窗口大小 |
| `OLLAMA_NUM_PREDICT` | `None` | 最大生成token數 |
| `OLLAMA_AUTO_PULL` | `1` | 自動下載模型（1=啟用） |

#### 使用場景

✅ **適合**:
- Agent 系統（Scammer, Expert, Victim）
- 複雜的多輪對話
- 需要精確控制生成參數
- 需要重試邏輯
- 需要自動模型管理
- 性能關鍵的場景

❌ **不適合**:
- 簡單的外部API調用（過於複雜）
- 不需要高級參數控制的場景

---

## 📊 對比分析

### 功能對比

| 功能 | /api/chat | /api/generate |
|-----|-----------|---------------|
| **端點類型** | FastAPI 包裝 | Ollama 原生 |
| **調用方式** | `requests.post()` | `httpx.AsyncClient` |
| **異步支持** | 部分（async 函數） | 完全異步 |
| **對話歷史** | 內建支持 | 需手動管理 |
| **超時時間** | 180秒 固定 | 300秒 可配置 |
| **重試邏輯** | ❌ 無 | ✅ 3次 + 指數退避 |
| **參數控制** | ❌ 基本 | ✅ 完整（temperature等） |
| **模型管理** | 環境變量 | 自動拉取 |
| **錯誤處理** | 簡單 | 詳細 + 日誌 |
| **串流輸出** | ❌ 不支持 | ✅ 支持 |

### 性能對比

| 指標 | /api/chat | /api/generate |
|-----|-----------|---------------|
| **連接管理** | 無連接池 | 連接池（max 10） |
| **請求延遲** | 中等 | 低（異步） |
| **並發能力** | 低 | 高 |
| **資源使用** | 中等 | 優化 |
| **適合場景** | 低頻調用 | 高頻調用 |

### 使用場景對比

#### `/api/chat` 適用場景

```python
# 示例：RPG Maker 對話
response = requests.post("http://localhost:8000/chat", json={
    "role": "你是一個友善的NPC商人",
    "message": "你好，你賣什麼？",
    "history": []
})
print(response.json()["reply"])
```

**適合**:
- 🎮 RPG Maker 插件
- 🌐 簡單的前端聊天
- 🔌 外部系統快速集成
- 📱 移動應用

#### `/api/generate` 適用場景

```python
# 示例：Agent 系統
from llms.ollama_llm import OllamaLlm

llm = OllamaLlm(model="gemma3:4b")
response = await llm.generate_content_async(llm_request)
```

**適合**:
- 🤖 Agent 對話系統（Scammer, Expert, Victim）
- 🎯 反詐騙模擬
- 🔬 Fine-Tuning 訓練數據生成
- ⚙️ 需要精確控制的場景

---

## 🔄 調用流程對比

### `/api/chat` 調用流程

```
1. 客戶端發送請求到 FastAPI
   POST /chat
   {role, message, history}

2. FastAPI 調用 call_ollama()
   - 構建 system prompt
   - 整合 history
   - 設置 model_name

3. requests.post() 到 Ollama
   POST http://localhost:11434/api/chat
   {model, messages, stream: false}

4. Ollama 處理請求
   - 加載模型
   - 生成回應

5. 返回結果
   {reply, success: true}
```

**時間**: ~2-10秒（取決於提示長度）

### `/api/generate` 調用流程

```
1. Agent 創建 LlmRequest
   LlmRequest(
     contents=[...],
     system_instruction="..."
   )

2. OllamaLlm.generate_content_async()
   - 提取文本
   - 配置參數
   - 自動拉取模型（如需）

3. 重試循環（最多3次）
   for attempt in range(3):
     try:
       POST /api/generate
       {model, prompt, system, options}
     except ConnectionError:
       等待並重試

4. Ollama 處理請求
   - 加載模型
   - 應用參數
   - 生成回應

5. 返回 LlmResponse
   包含生成的文本
```

**時間**: ~2-15秒（取決於提示長度和重試）

---

## 🛠️ 配置和優化

### `/api/chat` 配置

**環境變量**:
```bash
# .env 文件
AGENT_MODEL=gemma3:4b    # 使用的模型
```

**代碼配置**:
```python
# backend/api/chat_routes.py
OLLAMA_API_URL = "http://localhost:11434/api/chat"  # Ollama 地址
timeout=180  # 超時時間（秒）
```

### `/api/generate` 配置

**環境變量**:
```bash
# .env 文件
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_TEMPERATURE=0.5
OLLAMA_TOP_P=0.85
OLLAMA_REPEAT_PENALTY=1.1
OLLAMA_NUM_CTX=4096
OLLAMA_AUTO_PULL=1
```

**性能優化**:
```python
# 連接池配置
limits = httpx.Limits(
    max_keepalive_connections=5,
    max_connections=10
)

# 超時配置
timeout = httpx.Timeout(300.0, connect=30.0)
```

---

## 📝 最佳實踐

### 使用 `/api/chat` 時

✅ **推薦**:
```python
# 1. 保持 history 簡短（最多5輪）
history = recent_messages[-5:]

# 2. 使用有意義的 role
role = "你是一個專業的反詐騙顧問，用廣東話回應"

# 3. 處理錯誤
try:
    response = await chat(request)
except Exception as e:
    log.error(f"Chat failed: {e}")
```

❌ **避免**:
```python
# 不要傳遞過長的 history
history = all_messages  # ❌ 可能導致超時

# 不要省略 role
role = ""  # ❌ 回應質量低

# 不要忽略錯誤
response = await chat(request)  # ❌ 沒有錯誤處理
```

### 使用 `/api/generate` 時

✅ **推薦**:
```python
# 1. 使用環境變量配置參數
os.environ["OLLAMA_TEMPERATURE"] = "0.7"

# 2. 利用重試機制
# OllamaLlm 會自動重試，無需手動處理

# 3. 合理設置上下文窗口
os.environ["OLLAMA_NUM_CTX"] = "8192"  # 更長的對話
```

❌ **避免**:
```python
# 不要在代碼中硬編碼參數
# ❌ 應該使用環境變量

# 不要禁用自動拉取（除非確定模型已存在）
os.environ["OLLAMA_AUTO_PULL"] = "0"  # ❌

# 不要忽略日誌
# OllamaLlm 提供詳細日誌，應該監控
```

---

## 🔧 故障排除

### `/api/chat` 常見問題

#### 問題 1: 連接超時

**症狀**: `timeout after 180s`

**解決**:
```python
# 增加超時時間
response = requests.post(OLLAMA_API_URL, json=payload, timeout=300)
```

#### 問題 2: Ollama 未運行

**症狀**: `Connection refused`

**解決**:
```bash
# 啟動 Ollama
ollama serve
```

#### 問題 3: 模型未安裝

**症狀**: `model not found`

**解決**:
```bash
# 下載模型
ollama pull gemma3:4b
```

### `/api/generate` 常見問題

#### 問題 1: 重複重試失敗

**症狀**: 日誌顯示 `All 3 connection attempts failed`

**解決**:
```bash
# 1. 檢查 Ollama 服務
curl http://localhost:11434/api/tags

# 2. 重啟 Ollama
taskkill /F /IM ollama.exe
ollama serve

# 3. 檢查防火牆
```

#### 問題 2: 內存不足

**症狀**: `out of memory`

**解決**:
```bash
# 使用更小的模型
export AGENT_MODEL=gemma3:4b  # 而不是 27b

# 或減少上下文窗口
export OLLAMA_NUM_CTX=2048
```

---

## 📈 性能監控

### 監控指標

| 指標 | /api/chat | /api/generate |
|-----|-----------|---------------|
| **請求延遲** | 簡單監控 | 詳細日誌 |
| **成功率** | 需自己實現 | 內建重試統計 |
| **錯誤率** | 需自己實現 | 異常日誌 |
| **並發數** | 需自己實現 | 連接池監控 |

### 日誌示例

**`/api/chat`**:
```
INFO: Chat request received: role=..., message_len=50
INFO: Ollama response received: reply_len=120
```

**`/api/generate`**:
```
INFO: [OLLAMA] POST /api/generate base=http://localhost:11434 model=gemma3:4b prompt_len=256 system_len=150 attempt=1/3
INFO: [OLLAMA] response_len=180 status=200
```

---

## 🎯 總結

### 何時使用 `/api/chat`

✅ 簡單的外部客戶端集成  
✅ RPG Maker 或其他遊戲引擎  
✅ 不需要高級參數控制  
✅ 低頻調用（每分鐘 < 10次）  

### 何時使用 `/api/generate`

✅ 內部 Agent 系統  
✅ 需要精確控制生成參數  
✅ 需要重試和錯誤處理  
✅ 高頻調用（每分鐘 > 10次）  
✅ 性能關鍵的場景  

### 快速決策表

| 你的需求 | 推薦端點 |
|---------|---------|
| RPG Maker 對話 | `/api/chat` |
| 前端聊天界面 | `/api/chat` |
| Agent 對話系統 | `/api/generate` |
| Fine-Tuning 訓練 | `/api/generate` |
| 簡單原型開發 | `/api/chat` |
| 生產環境 Agent | `/api/generate` |

---

**文檔版本**: v1.0  
**最後更新**: 2024-11-11  
**維護者**: AI Agent Development Team

