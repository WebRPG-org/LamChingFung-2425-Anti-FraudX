# Anti-FraudX 完整部署詳細步驟指南

## 📋 目錄
1. [第一階段：GCP 準備](#第一階段gcp-準備)
2. [第二階段：代碼遷移](#第二階段代碼遷移)
3. [第三階段：容器化](#第三階段容器化)
4. [第四階段：後端部署](#第四階段後端部署)
5. [第五階段：前端部署](#第五階段前端部署)
6. [第六階段：域名配置](#第六階段域名配置)
7. [第七階段：監控設置](#第七階段監控設置)
8. [第八階段：測試上線](#第八階段測試上線)

---

## 第一階段：GCP 準備

### 步驟 1.1：創建 Google Cloud 項目

```bash
# 1. 安裝 Google Cloud CLI（如果還沒安裝）
# 下載地址：https://cloud.google.com/sdk/docs/install

# 2. 初始化 gcloud
gcloud init

# 3. 設置為當前項目（使用現有的 Gemini 專案）
gcloud config set project anti-fraudx

# 4. 驗證項目設置成功
gcloud projects describe anti-fraudx
```

### 步驟 1.2：啟用必要的 API

```bash
# 啟用所有必要的 API
gcloud services enable \
  run.googleapis.com \
  aiplatform.googleapis.com \
  firestore.googleapis.com \
  storage.googleapis.com \
  logging.googleapis.com \
  monitoring.googleapis.com \
  dns.googleapis.com \
  artifactregistry.googleapis.com \
  compute.googleapis.com \
  cloudresourcemanager.googleapis.com \
  --project=anti-fraudx

# 驗證 API 已啟用
gcloud services list --enabled
```

### 步驟 1.3：設置計費和配額

```bash
# 1. 驗證計費帳戶（應該已設置）
gcloud billing accounts list
gcloud billing projects describe anti-fraudx

# 2. 設置配額告警（防止超支）
# 進入 Google Cloud Console：https://console.cloud.google.com
# 導航到：Billing > Budgets and alerts
# 創建預算：$10/月（防止意外費用）
```

### 步驟 1.4：創建服務帳戶

```bash
# 1. 創建服務帳戶
gcloud iam service-accounts create anti-fraudx-sa \
  --display-name="Anti-FraudX Service Account" \
  --description="Service account for Anti-FraudX Cloud deployment"

# 2. 授予必要的角色
gcloud projects add-iam-policy-binding anti-fraudx \
  --member=serviceAccount:anti-fraudx-sa@anti-fraudx.iam.gserviceaccount.com \
  --role=roles/run.admin

gcloud projects add-iam-policy-binding anti-fraudx \
  --member=serviceAccount:anti-fraudx-sa@anti-fraudx.iam.gserviceaccount.com \
  --role=roles/aiplatform.user

gcloud projects add-iam-policy-binding anti-fraudx \
  --member=serviceAccount:anti-fraudx-sa@anti-fraudx.iam.gserviceaccount.com \
  --role=roles/datastore.user

gcloud projects add-iam-policy-binding anti-fraudx \
  --member=serviceAccount:anti-fraudx-sa@anti-fraudx.iam.gserviceaccount.com \
  --role=roles/storage.admin

# 3. 創建服務帳戶密鑰
gcloud iam service-accounts keys create ~/anti-fraudx-key.json \
  --iam-account=anti-fraudx-sa@anti-fraudx.iam.gserviceaccount.com

# 4. 設置認證環境變量
export GOOGLE_APPLICATION_CREDENTIALS=~/anti-fraudx-key.json

# 5. 驗證認證
gcloud auth application-default print-access-token
```

### 步驟 1.5：配置 Artifact Registry

```bash
# 1. 創建 Docker 倉庫
gcloud artifacts repositories create anti-fraudx-repo \
  --repository-format=docker \
  --location=us-central1 \
  --description="Docker repository for Anti-FraudX"

# 2. 配置 Docker 認證
gcloud auth configure-docker us-central1-docker.pkg.dev

# 3. 驗證倉庫
gcloud artifacts repositories list
```

### 步驟 1.6：創建 Firestore 數據庫

```bash
# 1. 創建 Firestore 數據庫
gcloud firestore databases create \
  --database=anti-fraudx-db \
  --location=us-central1 \
  --type=firestore-native

# 2. 驗證數據庫創建
gcloud firestore databases list
```

### 步驟 1.7：創建 Cloud Storage 存儲桶

```bash
# 1. 創建存儲桶
gsutil mb -l us-central1 gs://anti-fraudx-storage

# 2. 設置存儲桶權限
gsutil iam ch serviceAccount:anti-fraudx-sa@anti-fraudx.iam.gserviceaccount.com:objectAdmin gs://anti-fraudx-storage

# 3. 驗證存儲桶
gsutil ls
```

---

## 第二階段：代碼遷移

### 步驟 2.1：創建環境配置文件

#### 創建 `.env.local`（本地部署）

```bash
# 在 backend/ 目錄下創建 .env.local
cat > backend/.env.local << 'EOF'
# 部署環境
DEPLOYMENT_ENV=local
PROJECT_ID=anti-fraudx-local

# Gemini API 配置（本地用）
GEMINI_ENABLED=true
GEMINI_API_KEY=your_gemini_api_key_here

# Ollama 配置（本地備用）
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_ENABLED=false

# 數據庫配置
DATABASE_TYPE=sqlite
DATABASE_PATH=./anti_fraud_game.db

# 存儲配置
STORAGE_TYPE=local
STORAGE_PATH=./backend/uploads

# 應用配置
APP_ENV=development
DEBUG=true
LOG_LEVEL=INFO
EOF
```

#### 創建 `.env.cloud`（Cloud 部署）

```bash
# 在 backend/ 目錄下創建 .env.cloud
cat > backend/.env.cloud << 'EOF'
# 部署環境
DEPLOYMENT_ENV=cloud
PROJECT_ID=anti-fraudx

# GCP 配置
GCP_PROJECT_ID=anti-fraudx
GCP_LOCATION=us-central1

# Vertex AI 配置
USE_VERTEX_AI=true
VERTEX_AI_MODEL=gemini-3.1-flash
VERTEX_AI_TEMPERATURE=0.7
VERTEX_AI_TOP_P=0.95
VERTEX_AI_TOP_K=40
VERTEX_AI_MAX_TOKENS=2048

# Firestore 配置
DATABASE_TYPE=firestore
FIRESTORE_PROJECT_ID=anti-fraudx
FIRESTORE_DATABASE=anti-fraudx-db

# Cloud Storage 配置
STORAGE_TYPE=gcs
CLOUD_STORAGE_BUCKET=anti-fraudx-storage

# Cloud Run 配置
CLOUD_RUN_SERVICE=anti-fraudx-backend
CLOUD_RUN_REGION=us-central1

# 域名配置
DOMAIN_NAME=anti-fraudx.us.ci

# 應用配置
APP_ENV=production
DEBUG=false
LOG_LEVEL=WARNING
EOF
```

### 步驟 2.2：驗證 Vertex AI LLM 模塊

檢查 `backend/llms/vertex_ai_llm.py` 是否存在：

```bash
# 檢查文件
ls -la backend/llms/vertex_ai_llm.py

# 如果不存在，需要創建（見下面的代碼）
```

### 步驟 2.3：驗證 LLM Factory

檢查 `backend/llms/llm_factory.py` 是否已正確配置：

```bash
# 驗證 LLM Factory 支持 Cloud 部署
grep -n "DEPLOYMENT_ENV" backend/llms/llm_factory.py
grep -n "vertex_ai" backend/llms/llm_factory.py
```

### 步驟 2.4：更新 main.py

確保 `backend/main.py` 支持環境變量加載：

```bash
# 驗證環境變量加載
grep -n "load_dotenv" backend/main.py
grep -n "DEPLOYMENT_ENV" backend/main.py
```

### 步驟 2.5：本地測試 Vertex AI 連接

```bash
# 1. 設置認證
export GOOGLE_APPLICATION_CREDENTIALS=~/anti-fraudx-key.json

# 2. 設置環境變量
export DEPLOYMENT_ENV=cloud
export GCP_PROJECT_ID=anti-fraudx
export VERTEX_AI_MODEL=gemini-3.1-flash

# 3. 運行測試腳本
python backend/tests/test_vertex_ai_connection.py

# 4. 檢查輸出
# 應該看到：✅ Vertex AI 連接成功
```

---

## 第三階段：容器化

### 步驟 3.1：創建 Dockerfile.cloud

在項目根目錄創建 `Dockerfile.cloud`：

```dockerfile
# 使用 Python 3.11 官方鏡像
FROM python:3.11-slim

# 設置工作目錄
WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 複製 requirements
COPY backend/requirements-cloud.txt .

# 安裝 Python 依賴
RUN pip install --no-cache-dir -r requirements-cloud.txt

# 複製應用代碼
COPY backend/ /app/backend/
COPY rpg-platform-v2/ /app/rpg-platform-v2/
COPY frontend/ /app/frontend/

# 設置工作目錄為 backend
WORKDIR /app/backend

# 暴露端口
EXPOSE 8080

# 設置環境變量
ENV DEPLOYMENT_ENV=cloud
ENV PORT=8080

# 健康檢查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# 啟動應用
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### 步驟 3.2：構建容器鏡像

```bash
# 1. 設置項目 ID
export PROJECT_ID=anti-fraudx
export REGION=us-central1
export IMAGE_NAME=anti-fraudx-backend
export IMAGE_TAG=latest

# 2. 構建鏡像
docker build -f Dockerfile.cloud \
  -t ${REGION}-docker.pkg.dev/${PROJECT_ID}/anti-fraudx-repo/${IMAGE_NAME}:${IMAGE_TAG} \
  .

# 3. 驗證鏡像
docker images | grep anti-fraudx-backend
```

### 步驟 3.3：推送到 Artifact Registry

```bash
# 1. 配置 Docker 認證（如果還沒配置）
gcloud auth configure-docker us-central1-docker.pkg.dev

# 2. 推送鏡像
docker push us-central1-docker.pkg.dev/${PROJECT_ID}/anti-fraudx-repo/${IMAGE_NAME}:${IMAGE_TAG}

# 3. 驗證推送
gcloud artifacts docker images list us-central1-docker.pkg.dev/${PROJECT_ID}/anti-fraudx-repo
```

### 步驟 3.4：本地測試容器

```bash
# 1. 運行容器
docker run -it \
  -e DEPLOYMENT_ENV=cloud \
  -e GCP_PROJECT_ID=anti-fraudx \
  -e GOOGLE_APPLICATION_CREDENTIALS=/app/key.json \
  -v ~/anti-fraudx-key.json:/app/key.json \
  -p 8080:8080 \
  us-central1-docker.pkg.dev/${PROJECT_ID}/anti-fraudx-repo/${IMAGE_NAME}:${IMAGE_TAG}

# 2. 測試健康檢查
curl http://localhost:8080/health

# 3. 停止容器
# Ctrl+C
```

---

**下一部分將包含第四到第八階段的詳細步驟。**

