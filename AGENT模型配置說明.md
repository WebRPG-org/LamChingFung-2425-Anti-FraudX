# Agent 模型配置說明

## 📋 當前配置

根據環境變數檢查，當前系統使用的模型配置如下：

### 默認模型
- **基礎模型**: `gemma3:4b` (所有 Agent 的默認值)

### Fine-Tuned 模型（已配置）
- **ExpertAgent (專家)**: `anti-fraud-expert-20251111_220455`
- **ScammerAgent (騙徒)**: `anti-fraud-scammer-20251111_220455`
- **VictimAgent (受騙者)**: `gemma3:4b` (使用默認)
- **RecorderAgent (記錄人)**: `gemma3:4b` (使用默認)

---

## 🔧 模型配置邏輯

每個 Agent 的模型選擇遵循以下優先級：

1. **專用環境變數** (最高優先級)
   - `AGENT_MODEL_EXPERT` - 專家模型
   - `AGENT_MODEL_SCAMMER` - 騙徒模型
   - `AGENT_MODEL_VICTIM` - 受騙者模型
   - `AGENT_MODEL_RECORDER` - 記錄人模型

2. **通用環境變數** (次優先級)
   - `AGENT_MODEL` - 所有 Agent 的默認模型

3. **硬編碼默認值** (最低優先級)
   - `gemma3:4b` - 如果以上環境變數都未設置

---

## 📝 配置位置

### 環境變數文件
在以下位置創建或編輯 `.env` 文件來配置模型：

1. **項目根目錄** `.env`
2. **backend 目錄** `backend/.env`

### 配置示例

```bash
# ============================================
# 基礎模型配置（所有 Agent 共用）
# ============================================
AGENT_MODEL=gemma3:4b

# ============================================
# 各 Agent 獨立模型配置（可選）
# ============================================
# 使用 Fine-Tuned 模型
AGENT_MODEL_EXPERT=anti-fraud-expert-20251111_220455
AGENT_MODEL_SCAMMER=anti-fraud-scammer-20251111_220455

# 或使用其他模型
# AGENT_MODEL_EXPERT=gemma3:27b
# AGENT_MODEL_SCAMMER=mistral:7b

# ============================================
# Ollama 服務地址
# ============================================
OLLAMA_BASE_URL=http://localhost:11434
```

---

## 🎯 當前狀態

### ✅ 已配置 Fine-Tuned 模型
- **專家**: 使用 `anti-fraud-expert-20251111_220455` (Fine-Tuned)
- **騙徒**: 使用 `anti-fraud-scammer-20251111_220455` (Fine-Tuned)

### 📌 使用默認模型
- **受騙者**: 使用 `gemma3:4b` (基礎模型)
- **記錄人**: 使用 `gemma3:4b` (基礎模型)

---

## 🔄 如何更新模型配置

### 方法 1: 編輯 .env 文件

在 `backend/.env` 或項目根目錄的 `.env` 文件中添加：

```bash
# 使用最新的 Fine-Tuned 模型
AGENT_MODEL_EXPERT=anti-fraud-expert-20251111_220455
AGENT_MODEL_SCAMMER=anti-fraud-scammer-20251111_220455

# 或使用其他模型
AGENT_MODEL_VICTIM=gemma3:4b
AGENT_MODEL_RECORDER=gemma3:4b
```

### 方法 2: 使用環境變數（臨時）

```bash
# Windows PowerShell
$env:AGENT_MODEL_EXPERT="anti-fraud-expert-20251111_220455"
python start_server.py

# Windows CMD
set AGENT_MODEL_EXPERT=anti-fraud-expert-20251111_220455
python start_server.py
```

---

## 📊 模型列表

### 可用的 Fine-Tuned 模型
```bash
ollama list | findstr anti-fraud
```

當前可用的模型：
- `anti-fraud-expert-20251111_220455:latest`
- `anti-fraud-scammer-20251111_220455:latest`
- `anti-fraud-expert-20251111_220638:latest` (最新)

### 基礎模型
- `gemma3:4b` - 3.3 GB
- `gemma3:27b` - 17 GB
- `mistral:7b` - 4.4 GB

---

## 💡 建議配置

### 推薦配置（使用 Fine-Tuned 模型）

```bash
# 專家使用 Fine-Tuned 模型（更好的防騙建議）
AGENT_MODEL_EXPERT=anti-fraud-expert-20251111_220455

# 騙徒使用 Fine-Tuned 模型（更真實的詐騙話術）
AGENT_MODEL_SCAMMER=anti-fraud-scammer-20251111_220455

# 受騙者和記錄人使用基礎模型（節省資源）
AGENT_MODEL_VICTIM=gemma3:4b
AGENT_MODEL_RECORDER=gemma3:4b
```

### 高性能配置（所有 Agent 使用 Fine-Tuned 模型）

```bash
AGENT_MODEL_EXPERT=anti-fraud-expert-20251111_220455
AGENT_MODEL_SCAMMER=anti-fraud-scammer-20251111_220455
AGENT_MODEL_VICTIM=anti-fraud-expert-20251111_220455  # 也可以使用專家模型
AGENT_MODEL_RECORDER=anti-fraud-expert-20251111_220455  # 也可以使用專家模型
```

---

## 🔍 驗證配置

運行以下命令檢查當前配置：

```bash
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('Expert:', os.getenv('AGENT_MODEL_EXPERT', os.getenv('AGENT_MODEL', 'gemma3:4b'))); print('Scammer:', os.getenv('AGENT_MODEL_SCAMMER', os.getenv('AGENT_MODEL', 'gemma3:4b')))"
```

---

## 📚 相關文件

- `backend/agents/expert.py` - ExpertAgent 模型配置
- `backend/agents/scammer.py` - ScammerAgent 模型配置
- `backend/agents/victim.py` - VictimAgent 模型配置
- `backend/agents/recorder.py` - RecorderAgent 模型配置
- `ENV_配置說明.txt` - 環境變數詳細說明

---

**最後更新**: 2025-11-11

