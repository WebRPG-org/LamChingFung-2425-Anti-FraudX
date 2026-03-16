# Anti-FraudX 環境配置指南

## 概述

本項目支持雙環境部署：
- **本地部署**：使用 Gemini API 或 Ollama
- **Cloud 部署**：使用 Vertex AI Express Mode

## 環境變量配置

### 本地部署 (.env.local)

```bash
# 部署環境
DEPLOYMENT_ENV=local
PROJECT_ID=anti-fraudx-local
PROJECT_NAME=Anti-FraudX-Local

# Gemini API（本地用）
GEMINI_ENABLED=true
GEMINI_API_KEY=your_gemini_api_key_here

# Ollama（本地用）
OLLAMA_BASE_URL=http://localhost:11434
AGENT_MODEL=gemma3:4b

# 本地數據庫
DATABASE_TYPE=sqlite
DATABASE_PATH=./anti_fraud_game.db

# 本地存儲
STORAGE_TYPE=local
STORAGE_PATH=./backend/uploads

# 日誌
LOG_LEVEL=info
LOG_FILE=./backend/logs/anti-fraudx.log

# 應用設置
APP_NAME=Anti-FraudX
APP_VERSION=2.0.0
APP_ENV=development
```

### Cloud 部署 (.env.cloud)

```bash
# 部署環境
DEPLOYMENT_ENV=cloud
PROJECT_ID=anti-fraudx-us-ci
PROJECT_NAME=Anti-FraudX

# Google Cloud 設置
GCP_PROJECT_ID=anti-fraudx-us-ci
GCP_LOCATION=us-central1
GCP_REGION=us-central1

# Vertex AI（Cloud 用）
USE_VERTEX_AI=true
VERTEX_AI_MODEL=gemini-3.1-flash
VERTEX_AI_PROJECT=anti-fraudx-us-ci
VERTEX_AI_LOCATION=us-central1

# Firestore 數據庫
DATABASE_TYPE=firestore
FIRESTORE_PROJECT_ID=anti-fraudx-us-ci
FIRESTORE_DATABASE=anti-fraudx-db

# Cloud Storage
STORAGE_TYPE=gcs
CLOUD_STORAGE_BUCKET=anti-fraudx-storage
CLOUD_STORAGE_PROJECT=anti-fraudx-us-ci

# Cloud Run
CLOUD_RUN_SERVICE=anti-fraudx-backend
CLOUD_RUN_REGION=us-central1

# 域名
DOMAIN_NAME=anti-fraudx.us.ci
SSL_CERT_NAME=anti-fraudx-ssl-cert

# 服務帳戶
SERVICE_ACCOUNT=anti-fraudx-sa@anti-fraudx-us-ci.iam.gserviceaccount.com

# 日誌
LOG_LEVEL=info
CLOUD_LOGGING_ENABLED=true
LOG_SINK=anti-fraudx-logs

# 監控
MONITORING_ENABLED=true
MONITORING_DASHBOARD=anti-fraudx-dashboard

# 應用設置
APP_NAME=Anti-FraudX
APP_VERSION=2.0.0
APP_ENV=production
```

## 設置步驟

### 1. 本地部署

```bash
# 複製模板
cp .env.example .env.local

# 編輯 .env.local，填入你的 Gemini API Key
# GEMINI_API_KEY=your_actual_key_here

# 啟動本地服務
docker-compose -f docker-compose.local.yml up
```

### 2. Cloud 部署

```bash
# 複製模板
cp .env.example .env.cloud

# 編輯 .env.cloud，填入 GCP 項目信息
# GCP_PROJECT_ID=anti-fraudx-us-ci

# 初始化 GCP
bash deploy/cloud/setup_gcp.sh

# 部署到 Cloud Run
bash deploy/cloud/deploy_to_cloud.sh
```

## 環境變量說明

| 變量 | 本地 | Cloud | 說明 |
|------|------|-------|------|
| DEPLOYMENT_ENV | local | cloud | 部署環境 |
| DATABASE_TYPE | sqlite | firestore | 數據庫類型 |
| STORAGE_TYPE | local | gcs | 存儲類型 |
| USE_VERTEX_AI | false | true | 使用 Vertex AI |
| GEMINI_ENABLED | true | false | 使用 Gemini API |

## 自動環境選擇

系統會根據 `DEPLOYMENT_ENV` 自動選擇：

```python
# backend/llms/llm_factory.py
if deployment_env == "cloud":
    # 使用 Vertex AI Express Mode
    from llms.vertex_ai_llm import VertexAILLM
else:
    # 使用 Gemini API 或 Ollama
    from llms.gemini_llm import GeminiLLM
```

## 常見問題

### Q: 如何在本地測試 Cloud 配置？

A: 使用 `docker-compose.cloud.yml`：

```bash
docker-compose -f docker-compose.cloud.yml up
```

### Q: 如何切換 LLM 提供者？

A: 編輯環境變量：

```bash
# 使用 Gemini API
GEMINI_ENABLED=true

# 使用 Ollama
GEMINI_ENABLED=false
OLLAMA_BASE_URL=http://localhost:11434
```

### Q: 如何在 Cloud 上使用本地 Ollama？

A: 這不推薦，但可以通過設置 `OLLAMA_BASE_URL` 指向公開的 Ollama 實例。

## 安全建議

1. **不要提交 .env 文件**：已在 `.gitignore` 中
2. **使用 Secret Manager**：在 Cloud 上使用 Google Secret Manager
3. **定期輪換密鑰**：定期更新 API Key
4. **監控成本**：設置計費告警

## 更多信息

- [本地部署指南](docs/LOCAL_DEPLOYMENT.md)
- [Cloud 部署指南](docs/CLOUD_DEPLOYMENT.md)
- [命名規範](docs/NAMING_CONVENTION.md)

