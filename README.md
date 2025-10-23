# AI-Agents multi agent

多智能體（騙徒 / 受騙者 / 防騙專家 / 記錄人）真實對話模擬，支援 WebSocket 實時顯示、循環訓練、RAG、以及基於 Ollama 的本地大模型（Gemma3 4B/27B）。

## 快速開始（本機）

1) 安裝必備
- 安裝 Python 3.10+（建議 3.11/3.12/3.13）
- 安裝 [Ollama](https://ollama.com)
- 拉取模型（最少一個）：

```bash
ollama pull gemma3:4b
# 或
ollama pull gemma3:27b
```

2) 安裝後端依賴

```bash
pip install -r backend/requirements.txt
```

3) 建立環境變數檔（可直接複製 `.env.example` 內容）

```bash
# 建議放在 backend/.env（或專案根目錄 .env）
# 例：全部 Agent 使用 27B 並連到本機 11434
AGENT_MODEL=gemma3:27b
OLLAMA_BASE_URL=http://127.0.0.1:11434

# 若要每個 Agent 指向不同 Ollama 端口（可提升 VRAM 利用率）
AGENT_MODEL_SCAMMER=gemma3:27b
AGENT_MODEL_VICTIM=gemma3:27b
AGENT_MODEL_EXPERT=gemma3:27b
AGENT_MODEL_RECORDER=gemma3:27b
OLLAMA_BASE_URL_SCAMMER=http://127.0.0.1:11434
OLLAMA_BASE_URL_VICTIM=http://127.0.0.1:11435
OLLAMA_BASE_URL_EXPERT=http://127.0.0.1:11436
OLLAMA_BASE_URL_RECORDER=http://127.0.0.1:11437
```

4) 啟動服務

```bash
python start_server.py
```

啟動後開啟瀏覽器：`http://127.0.0.1:8000`（Web UI）

## Docker（開發）

```bash
docker compose up -d
# 停用
docker compose down
```

Compose 會綁定 `backend/` 與 `frontend/` 以利熱更新。

## Web UI 使用
- 詐騙手法 / 受騙者類型：可選隨機或指定
- 模式：
  - 加速（fast）：最快速實時顯示
  - 演示（demo）：每位 Agent 回覆後延遲 3–5 秒
- 按鈕：
  - 開始對話：單場模擬
  - 循環訓練：後台持續產生訓練資料
  - 停止訓練（本輪後）：等待當前輪完成
  - 立即停止：立刻結束本輪，保存已產生內容

## 主要 API（節選）

- 啟動單場模擬（回傳 `simulation_id` 與 WS URL）

```bash
curl -X POST http://127.0.0.1:8000/simulation/start \
  -H "Content-Type: application/json" \
  -d '{"victim_persona":"average","scam_tactic":"WhatsApp 對話詐騙","mode":"fast"}'
```

- 循環訓練

```bash
curl -X POST http://127.0.0.1:8000/api/training/loop/start -H "Content-Type: application/json" -d '{"interval_seconds":0.1,"mode":"fast"}'
curl -X POST http://127.0.0.1:8000/api/training/loop/stop
curl http://127.0.0.1:8000/api/training/status
```

## 多 Ollama 實例（可選）

為每位 Agent 啟動獨立 Ollama 實例可提升 VRAM 使用效率（Windows PowerShell 範例）：

```powershell
$env:OLLAMA_HOST = '127.0.0.1:11434'; ollama serve
$env:OLLAMA_HOST = '127.0.0.1:11435'; ollama serve
$env:OLLAMA_HOST = '127.0.0.1:11436'; ollama serve
$env:OLLAMA_HOST = '127.0.0.1:11437'; ollama serve
```

設定對應的 `OLLAMA_BASE_URL_*` 即可。

## 模型微調與分發（可選）

```bash
python backend/scripts/model_fine_tuning.py
cd backend/models
./deploy.sh
```



