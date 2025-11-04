# AI-Agents multi agent

多智能體（騙徒 / 受騙者 / 防騙專家 / 記錄人）真實對話模擬，支援 WebSocket 實時顯示、循環訓練、RAG、以及基於 Ollama 的本地大模型（Gemma3 4B/27B, Mistral 7B）。

## 快速開始（本機）

1) 安裝必備
- 安裝 Python 3.10+（建議 3.11/3.12/3.13）
- 安裝 [Ollama](https://ollama.com)
- 拉取模型

```bash
ollama pull gemma3:4b
ollama pull mistral:7b
```

2) 安裝後端依賴

```bash
pip install -r backend/requirements.txt
```

3) 建立環境變數檔

在專案根目錄或 `backend/` 目錄創建 `.env` 文件：

```bash
# ============================================
# Ollama 模型配置
# ============================================
# 基礎模型配置（所有 Agent 共用，除非下面有單獨配置）
AGENT_MODEL=gemma3:4b
# 或使用其他模型
# AGENT_MODEL=gemma3:27b
# AGENT_MODEL=mistral:7b

# Ollama 服務地址
OLLAMA_BASE_URL=http://127.0.0.1:11434

# ============================================
# 各 Agent 獨立模型配置（可選，提升 VRAM 利用率）
# ============================================
# 若未設定，將使用上面的 AGENT_MODEL
AGENT_MODEL_SCAMMER=gemma3:4b
AGENT_MODEL_VICTIM=gemma3:4b
AGENT_MODEL_EXPERT=gemma3:4b
AGENT_MODEL_RECORDER=gemma3:4b

# 各 Agent 獨立的 Ollama 服務地址（可選）
# 適用於多 Ollama 實例場景
OLLAMA_BASE_URL_SCAMMER=http://127.0.0.1:11434
OLLAMA_BASE_URL_VICTIM=http://127.0.0.1:11435
OLLAMA_BASE_URL_EXPERT=http://127.0.0.1:11436
OLLAMA_BASE_URL_RECORDER=http://127.0.0.1:11437

# ============================================
# 自動訓練設定
# ============================================
# 對話結束後自動開始新一輪（預設啟用）
AUTO_TRAIN_ENABLED=true  # true: 啟用, false: 禁用

# ============================================
# GPU 配置（Docker 環境）
# ============================================
# 是否強制使用 GPU（Docker 環境）
FORCE_GPU=1  # 1: 強制使用 GPU, 0: 允許 CPU

# ============================================
# 應用配置
# ============================================
# 應用環境
APP_ENV=development  # development | production

# 日誌級別（Docker 環境，必須小寫）
LOG_LEVEL=info  # info | debug | warning | error

# Python 配置
PYTHONPATH=/app/backend  # Docker 環境
PYTHONUNBUFFERED=1  # 即時輸出日誌
```

**配置說明：**
- **本地開發**：將 `.env` 放在專案根目錄或 `backend/` 目錄
- **Docker 環境**：`.env` 文件會被 Docker Compose 自動讀取
- **模型選擇**：支援 `gemma3:4b`, `gemma3:27b`, `mistral:7b` 等 Ollama 模型
- **多實例模式**：可為每個 Agent 配置不同的模型和 Ollama 實例，提升 GPU 利用率

4) 啟動服務

```bash
python start_server.py
```

啟動後開啟瀏覽器：`http://127.0.0.1:8000`（Web UI）

## Docker 部署

### 開發環境（推薦）

使用 `docker-compose.yml`（包含 Ollama 容器）或 `docker-compose.local.yml`（使用本地 Ollama）：

```bash
# 方式 1: 完整容器化（包含 Ollama）
docker compose up -d

# 方式 2: 使用本地 Ollama（Windows 推薦）
docker compose -f docker-compose.local.yml up -d

# 方式 3: 開發環境（熱重載）
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# 停用
docker compose down
```

**開發環境特點：**
- 代碼熱重載（修改代碼後自動重啟）
- 綁定 `backend/` 與 `frontend/` 目錄
- 數據持久化到本地

### 生產環境

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

**生產環境特點：**
- 多 worker 進程（預設 4 個）
- 資源限制配置
- 日誌輪轉和壓縮
- 不使用代碼掛載（使用鏡像內代碼）

### Docker 配置說明

- **docker-compose.yml**: 基礎配置（包含 Ollama 和 Backend）
- **docker-compose.local.yml**: 本地開發（使用主機上的 Ollama）
- **docker-compose.dev.yml**: 開發環境擴展（熱重載、調試端口）
- **docker-compose.prod.yml**: 生產環境擴展（多 worker、資源限制）

### 數據持久化

Docker Compose 會自動創建以下數據卷：
- `training_data`: 訓練數據
- `models_data`: 模型文件
- `db_data`: 數據庫文件
- `arms_race_data`: 軍備競賽數據
- `agent_versions`: Agent 版本歷史
- `ab_test_results`: A/B 測試結果
- `ollama_models`: Ollama 模型文件

### GPU 支援

確保已安裝 NVIDIA Docker Runtime：
```bash
# 檢查 GPU 是否可用
docker run --rm --gpus all nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi
```

## Web UI 使用
- 詐騙手法 / 受騙者類型：可選隨機或指定
- 模式：
  - 加速（fast）：最快速實時顯示
  - 演示（demo）：每位 Agent 回覆後延遲 3–5 秒
- 自動訓練：對話結束後自動開始新一輪（可在環境變數中設定 `AUTO_TRAIN_ENABLED=false` 禁用）
- 按鈕：
  - 開始對話：單場模擬（支援自動訓練）
  - 停止對話：立即停止當前對話，保存已產生內容

## 主要 API（節選）

- 啟動單場模擬（回傳 `simulation_id` 與 WS URL）

```bash
curl -X POST http://127.0.0.1:8000/simulation/start \
  -H "Content-Type: application/json" \
  -d '{"victim_persona":"average","scam_tactic":"WhatsApp 對話詐騙","mode":"fast","auto_train":true}'
```

**參數說明：**
- `victim_persona`: `"elderly"` | `"average"` | `"overconfident"` | `"random"`
- `scam_tactic`: 詐騙手法（如 `"WhatsApp 對話詐騙"`）或 `"random"`
- `mode`: `"fast"` | `"demo"`
- `auto_train`: `true` | `false`（是否啟用自動訓練，預設為 `true`）

- 停止當前模擬（通過 WebSocket 發送 `stop_now` 命令）

## 多 Ollama 實例（可選）

為每位 Agent 啟動獨立 Ollama 實例可提升 VRAM 使用效率（Windows PowerShell 範例）：

```powershell
$env:OLLAMA_HOST = '127.0.0.1:11434'; ollama serve
$env:OLLAMA_HOST = '127.0.0.1:11435'; ollama serve
$env:OLLAMA_HOST = '127.0.0.1:11436'; ollama serve
$env:OLLAMA_HOST = '127.0.0.1:11437'; ollama serve
```

設定對應的 `OLLAMA_BASE_URL_*` 即可。

## 核心功能

### 動態信任系統
- 受騙者對騙徒和專家的信任度實時變化（0-100分）
- 信任度影響對話走向和行為決策
- 信任度達到臨界值時自動觸發勝利條件

### 角色一致性保證
- 嚴格的角色一致性檢查機制
- 自動檢測並修正角色混亂、重複對話等問題
- 確保每個 Agent 嚴格遵守角色設定

### 自動訓練系統
- 對話結束後自動開始新一輪（可選）
- 隨機選擇受害者類型和詐騙手法
- 持續收集訓練數據用於軍備競賽系統

### 軍備競賽系統
- 騙徒和專家通過對抗學習持續進化
- 分析訓練數據提取成功/失敗模式
- 自動生成進化策略並應用到 Agent

**使用快速進化工具：**
```bash
快速进化.bat
# 選擇 [1] 完整進化流程（分析 + 應用）
```

## 模型微調與分發（可選）

```bash
python backend/scripts/model_fine_tuning.py
cd backend/models
./deploy.sh
```

## 相關文檔

- **項目架構文檔**: `项目架构文档.md` - 詳細的系統架構和技術說明
- **RPG Maker 整合**: `RPG_MAKER_整合指南.md` - RPG Maker 遊戲整合指南



