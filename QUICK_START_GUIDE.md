# AI 防詐平台 v4.1 - 快速啟動指南

## 🚀 5分鐘快速開始

### 前置要求
- Python 3.8+
- Node.js 16+
- Ollama（本地模式）或 Gemini API 密鑰（雲端模式）
- SQLite3
- ChromaDB

### 步驟 1：環境設置（2分鐘）

```bash
# 1. 進入項目目錄
cd "C:\Users\andy1\Desktop\新增資料夾 (2)\AI-Agent-main v9-3-11-26\AI-Agent-main"

# 2. 創建虛擬環境（如果還沒有）
python -m venv venv
venv\Scripts\activate

# 3. 安裝依賴
pip install -r backend/requirements.txt

# 4. 驗證安裝
python -c "from backend.config import config; print('✅ Config OK')"
```

### 步驟 2：配置環境變量（1分鐘）

編輯 `backend/.env`：

```bash
# LLM 配置
GEMINI_ENABLED=false
AGENT_MODEL=gemma3:4b
OLLAMA_BASE_URL=http://localhost:11434

# 性能配置
OLLAMA_NUM_CTX=2048
OLLAMA_NUM_PREDICT=400
OLLAMA_TEMPERATURE=0.7

# 數據庫配置
DATABASE_PATH=anti_fraud_game.db
CHROMA_PATH=backend/db/chroma_db

# 功能開關
ENABLE_RAG=true
ENABLE_ADAPTIVE_SCORING=true
ENABLE_PARALLEL_GENERATION=true
```

### 步驟 3：啟動後端（1分鐘）

```bash
# 進入後端目錄
cd backend

# 啟動 FastAPI 服務器
python main.py

# 預期輸出：
# INFO:     Uvicorn running on http://127.0.0.1:8000
# ✅ Loaded 15 routers successfully
```

### 步驟 4：啟動前端（1分鐘）

在新的終端窗口：

```bash
# 進入前端目錄
cd rpg-platform-v2

# 安裝依賴（首次）
npm install

# 啟動開發服務器
npm run dev

# 預期輸出：
# VITE v4.x.x  ready in xxx ms
# ➜  Local:   http://localhost:3000
```

### 步驟 5：訪問應用（0分鐘）

打開瀏覽器訪問：
- **遊戲**: http://localhost:3000
- **API 文檔**: http://localhost:8000/docs

---

## 🧪 驗證系統是否正常運行

### 驗證 1：後端健康檢查

```bash
# 在新的終端窗口執行
curl http://localhost:8000/health

# 預期輸出：
# {"status":"Backend is running","model_in_use":"gemma3:4b"}
```

### 驗證 2：測試 API 端點

```bash
# 測試遊戲開始
curl -X POST http://localhost:8000/api/rpgv2/game/start \
  -H "Content-Type: application/json" \
  -d '{"persona_type":"B","scam_type":"banking"}'

# 預期輸出：
# {"session_id":"xxx","success":true,"opening_messages":[...]}
```

### 驗證 3：測試四代理系統

```python
# 在 Python 中測試
from backend.services.agent_service import AgentService

service = AgentService(persona_type="average")
session_id = service.create_session()

# 測試騙徒
scammer_result = await service.generate_response(
    agent_type="scammer",
    message="",
    session_id=session_id
)
print(f"✅ Scammer: {scammer_result['reply'][:50]}...")

# 測試專家
expert_result = await service.generate_response(
    agent_type="expert",
    message="你好",
    session_id=session_id
)
print(f"✅ Expert: {expert_result['reply'][:50]}...")

# 測試受害者
victim_result = await service.generate_response(
    agent_type="victim",
    message="你好",
    session_id=session_id
)
print(f"✅ Victim: {victim_result['reply'][:50]}...")
```

### 驗證 4：測試信任度系統

```python
from backend.utils.performance_tracker import PerformanceTracker

tracker = PerformanceTracker(victim_persona="elderly")

# 測試信任度更新
result = tracker.update_trust(
    scammer_text="你好，我係銀行職員",
    expert_text="婆婆唔使驚，呢個係騙局",
    victim_text="係咪真嘅？"
)

print(f"✅ Trust in scammer: {result['trust_in_scammer']}")
print(f"✅ Trust in expert: {result['trust_in_expert']}")
print(f"✅ Alertness: {result['alertness']}")
```

### 驗證 5：測試並行生成

```python
import asyncio
from backend.services.agent_service import AgentService

async def test_parallel_generation():
    service = AgentService(persona_type="average")
    session_id = service.create_session()
    
    # 測試並行生成
    import time
    start = time.time()
    
    scammer_task = service.generate_response(
        agent_type="scammer",
        message="",
        session_id=session_id
    )
    
    expert_task = service.generate_response(
        agent_type="expert",
        message="",
        session_id=session_id
    )
    
    scammer_result, expert_result = await asyncio.gather(
        scammer_task,
        expert_task
    )
    
    elapsed = time.time() - start
    print(f"✅ Parallel generation completed in {elapsed:.2f}s")
    print(f"✅ Scammer: {scammer_result['reply'][:30]}...")
    print(f"✅ Expert: {expert_result['reply'][:30]}...")

asyncio.run(test_parallel_generation())
```

---

## 📊 性能基準測試

### 測試並行生成性能提升

```bash
# 創建測試腳本 test_performance.py
python test_performance.py

# 預期結果：
# 順序執行: 8-16 秒
# 並行執行: 4-8 秒
# 性能提升: ~50%
```

### 測試 RAG 查詢性能

```bash
# 測試 RAG 查詢時間
python -c "
from backend.llms.rag_integration import GeminiRAGHelper
import time

helper = GeminiRAGHelper()
start = time.time()
context = helper.get_rag_context('假冒銀行')
elapsed = time.time() - start

print(f'✅ RAG query time: {elapsed:.2f}s')
print(f'✅ Context length: {len(context)} chars')
"
```

---

## 🎮 測試遊戲流程

### 完整遊戲測試

```bash
# 1. 打開瀏覽器訪問 http://localhost:3000
# 2. 選擇遊戲模式（騙徒模式、專家模式、自動模式）
# 3. 選擇受害者類型（長者、普通人、過度自信、學生）
# 4. 選擇詐騙類型（假冒銀行、假冒政府等）
# 5. 開始遊戲
# 6. 輸入消息並觀察 AI 回應
# 7. 檢查信任度變化
# 8. 遊戲結束後查看分析報告
```

### 自動模式測試

```bash
# 測試自動模式（AI vs AI）
curl -X POST http://localhost:8000/api/rpgv2/game/auto-play \
  -H "Content-Type: application/json" \
  -d '{
    "session_id":"test_auto",
    "rounds":5
  }'

# 預期輸出：
# {"success":true,"messages":[...],"game_state":{...}}
```

---

## 🔍 調試技巧

### 查看日誌

```bash
# 查看實時日誌
tail -f backend/logs/error.log

# 查看特定級別的日誌
grep "ERROR" backend/logs/error.log
grep "WARNING" backend/logs/error.log
```

### 啟用詳細日誌

編輯 `backend/.env`：
```bash
LOG_LEVEL=DEBUG
```

### 使用 Python 調試器

```python
# 在代碼中添加斷點
import pdb; pdb.set_trace()

# 或使用 VS Code 調試器
# 在 .vscode/launch.json 中配置
```

---

## 🐛 常見問題排查

### 問題 1：Ollama 連接失敗

```bash
# 檢查 Ollama 是否運行
curl http://localhost:11434/api/tags

# 如果失敗，啟動 Ollama
ollama serve

# 拉取模型
ollama pull gemma3:4b
```

### 問題 2：Gemini API 密鑰無效

```bash
# 驗證 API 密鑰
python -c "
from backend.config import config
print(f'Gemini enabled: {config.gemini.GEMINI_ENABLED}')
print(f'API key configured: {bool(config.gemini.GEMINI_API_KEY)}')
"
```

### 問題 3：數據庫錯誤

```bash
# 重置數據庫
rm anti_fraud_game.db
python -c "from backend.api.game_routes_v2 import init_database; init_database()"
```

### 問題 4：ChromaDB 加載失敗

```bash
# 檢查 ChromaDB 路徑
python -c "
from backend.config import config
print(f'ChromaDB path: {config.database.CHROMA_PATH}')
import os
print(f'Path exists: {os.path.exists(config.database.CHROMA_PATH)}')
"

# 重新初始化 ChromaDB
rm -rf backend/db/chroma_db
python scripts/initialize_chromadb.py
```

---

## 📈 監控系統健康狀態

### 實時監控儀表板

```bash
# 啟動監控服務
python backend/utils/health_monitor.py

# 預期輸出：
# ✅ Backend: OK
# ✅ Database: OK
# ✅ ChromaDB: OK
# ✅ Ollama: OK
# ✅ Memory: 45%
# ✅ CPU: 12%
```

### 性能指標

```bash
# 查看性能指標
curl http://localhost:8000/api/metrics

# 預期輸出：
# {
#   "avg_response_time": 2.5,
#   "total_requests": 1234,
#   "error_rate": 0.1,
#   "parallel_generation_speedup": 1.5
# }
```

---

## 🚀 部署到生產環境

### Docker 部署

```bash
# 構建 Docker 鏡像
docker build -t anti-fraud-platform:v4.1 .

# 運行容器
docker run -p 8000:8000 -p 3000:3000 \
  -e GEMINI_ENABLED=false \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  anti-fraud-platform:v4.1
```

### Cloud Run 部署

```bash
# 部署到 Google Cloud Run
gcloud run deploy anti-fraudx-backend \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --timeout 3600 \
  --memory 2Gi \
  --cpu 2
```

---

## 📞 獲取幫助

### 查看文檔

- `IMPLEMENTATION_GUIDE_v4.1.md` - 完整實施指南
- `CODE_IMPLEMENTATION_CHECKLIST.md` - 代碼實施清單
- `docs/CORE_FEATURES.md` - 核心功能文檔
- `docs/ARCHITECTURE.md` - 系統架構文檔

### 聯繫支持

- 提交 Issue：GitHub Issues
- 發送郵件：support@anti-fraud-platform.com
- 加入社區：Discord 頻道

---

## ✅ 完成檢查清單

在開始開發前，請確保：

- [ ] Python 環境已設置
- [ ] 所有依賴已安裝
- [ ] 環境變量已配置
- [ ] 後端能正常啟動
- [ ] 前端能正常啟動
- [ ] API 端點能正常訪問
- [ ] 四代理系統能正常生成回應
- [ ] 信任度系統能正常計算
- [ ] 並行生成能正常執行
- [ ] 會話持久化能正常工作
- [ ] 所有測試都通過

---

## 🎉 下一步

完成上述驗證後，你可以：

1. **開始開發** - 按照 `CODE_IMPLEMENTATION_CHECKLIST.md` 逐步完善系統
2. **運行測試** - 執行單元測試和集成測試
3. **性能優化** - 根據基準測試結果優化性能
4. **部署上線** - 部署到生產環境

祝你開發順利！🚀
