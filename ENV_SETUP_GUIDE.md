# Anti-FraudX 環境配置設置指南

## 快速開始

### 本地部署

1. **複製環境模板**
```bash
cp .env.example backend/.env.local
```

2. **編輯 backend/.env.local**
```bash
DEPLOYMENT_ENV=local
PROJECT_ID=anti-fraudx-local
GEMINI_ENABLED=true
GEMINI_API_KEY=your_actual_gemini_api_key_here
OLLAMA_BASE_URL=http://localhost:11434
AGENT_MODEL=gemma3:4b
DATABASE_TYPE=sqlite
DATABASE_PATH=./anti_fraud_game.db
STORAGE_TYPE=local
STORAGE_PATH=./backend/uploads
APP_ENV=development
```

3. **啟動本地服務**
```bash
# 使用 Docker Compose
docker-compose -f docker-compose.local.yml up

# 或直接運行
cd backend
python main.py
```

### Cloud 部署

1. **複製環境模板**
```bash
cp .env.example backend/.env.cloud
```

2. **編輯 backend/.env.cloud**
```bash
DEPLOYMENT_ENV=cloud
PROJECT_ID=anti-fraudx-us-ci
GCP_PROJECT_ID=anti-fraudx-us-ci
GCP_LOCATION=us-central1
USE_VERTEX_AI=true
VERTEX_AI_MODEL=gemini-3.1-flash
DATABASE_TYPE=firestore
FIRESTORE_PROJECT_ID=anti-fraudx-us-ci
FIRESTORE_DATABASE=anti-fraudx-db
STORAGE_TYPE=gcs
CLOUD_STORAGE_BUCKET=anti-fraudx-storage
CLOUD_RUN_SERVICE=anti-fraudx-backend
DOMAIN_NAME=anti-fraudx.us.ci
APP_ENV=production
```

3. **初始化 GCP**
```bash
bash deploy/cloud/setup_gcp.sh
```

4. **部署到 Cloud Run**
```bash
bash deploy/cloud/deploy_to_cloud.sh
```

## 環境變量說明

### 部署環境
- `DEPLOYMENT_ENV`: 部署環境（local 或 cloud）

### 項目信息
- `PROJECT_ID`: 項目 ID
- `APP_NAME`: 應用名稱
- `APP_VERSION`: 應用版本
- `APP_ENV`: 應用環境（development 或 production）

### 本地配置
- `GEMINI_ENABLED`: 是否啟用 Gemini API
- `GEMINI_API_KEY`: Gemini API Key
- `OLLAMA_BASE_URL`: Ollama 服務 URL
- `AGENT_MODEL`: Agent 模型名稱

### Cloud 配置
- `GCP_PROJECT_ID`: Google Cloud 項目 ID
- `GCP_LOCATION`: Google Cloud 區域
- `USE_VERTEX_AI`: 是否使用 Vertex AI
- `VERTEX_AI_MODEL`: Vertex AI 模型名稱

### 數據庫配置
- `DATABASE_TYPE`: 數據庫類型（sqlite 或 firestore）
- `DATABASE_PATH`: SQLite 數據庫路徑（本地用）
- `FIRESTORE_PROJECT_ID`: Firestore 項目 ID（Cloud 用）
- `FIRESTORE_DATABASE`: Firestore 數據庫名稱（Cloud 用）

### 存儲配置
- `STORAGE_TYPE`: 存儲類型（local 或 gcs）
- `STORAGE_PATH`: 本地存儲路徑（本地用）
- `CLOUD_STORAGE_BUCKET`: Cloud Storage 桶名稱（Cloud 用）

### 其他配置
- `DOMAIN_NAME`: 域名
- `LOG_LEVEL`: 日誌級別
- `CLOUD_RUN_SERVICE`: Cloud Run 服務名稱

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

### Q: 環境變量在哪裡設置？
A: 
- 本地：`backend/.env.local`
- Cloud：`backend/.env.cloud`
- Docker：在 `docker-compose.yml` 中設置

### Q: 如何驗證環境配置？
A: 啟動應用後，查看日誌中的環境信息：
```
==================================================
Anti-FraudX 環境配置
==================================================
環境: LOCAL
項目 ID: anti-fraudx-local
應用名稱: Anti-FraudX
應用版本: 2.0.0
應用環境: development
域名: localhost
日誌級別: info
==================================================
```

## 安全建議

1. **不要提交 .env 文件**
   - 已在 `.gitignore` 中排除
   - 使用 `.env.example` 作為模板

2. **保護敏感信息**
   - 不要在代碼中硬編碼 API Key
   - 使用環境變量或 Secret Manager

3. **定期輪換密鑰**
   - 定期更新 Gemini API Key
   - 定期更新 GCP 服務帳戶密鑰

4. **監控成本**
   - 設置計費告警
   - 定期檢查 Cloud 成本

## 驗證部署

### 本地驗證
```bash
# 檢查環境變量
echo $DEPLOYMENT_ENV

# 訪問應用
curl http://localhost:8000/health
```

### Cloud 驗證
```bash
# 檢查 Cloud Run 服務
gcloud run services describe anti-fraudx-backend \
  --platform managed \
  --region us-central1

# 測試 API
curl https://anti-fraudx.us.ci/health
```

## 下一步

1. ✅ 配置環境變量
2. ✅ 啟動應用
3. ✅ 驗證部署
4. ✅ 進行功能測試
5. ✅ 監控性能


