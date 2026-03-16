# Anti-FraudX 部署指南 - Windows PowerShell 版本

## ⚠️ 重要提示

如果你在 Windows 上使用 PowerShell，請使用本指南中的命令。
如果你使用 Git Bash 或 WSL，可以使用原始的 bash 命令。

---

## 第一階段：GCP 準備 - Windows PowerShell 版本

### 步驟 1.1：初始化 gcloud

```powershell
# 初始化 gcloud
gcloud init

# 設置為當前項目
gcloud config set project anti-fraudx

# 驗證項目設置成功
gcloud projects describe anti-fraudx
```

### 步驟 1.2：啟用必要的 API

```powershell
# 方法 1：單行命令（推薦）
gcloud services enable run.googleapis.com aiplatform.googleapis.com firestore.googleapis.com storage.googleapis.com logging.googleapis.com monitoring.googleapis.com dns.googleapis.com artifactregistry.googleapis.com compute.googleapis.com cloudresourcemanager.googleapis.com

# 方法 2：使用 PowerShell 反引號續行
gcloud services enable `
  run.googleapis.com `
  aiplatform.googleapis.com `
  firestore.googleapis.com `
  storage.googleapis.com `
  logging.googleapis.com `
  monitoring.googleapis.com `
  dns.googleapis.com `
  artifactregistry.googleapis.com `
  compute.googleapis.com `
  cloudresourcemanager.googleapis.com

# 驗證 API 已啟用
gcloud services list --enabled
```

### 步驟 1.3：設置計費和配額

```powershell
# 驗證計費帳戶
gcloud billing accounts list
gcloud billing projects describe anti-fraudx

# 設置配額告警
# 進入 Google Cloud Console：https://console.cloud.google.com
# 導航到：Billing > Budgets and alerts
# 創建預算：$10/月（防止意外費用）
```

### 步驟 1.4：創建服務帳戶

```powershell
# 創建服務帳戶（單行）
gcloud iam service-accounts create anti-fraudx-sa --display-name="Anti-FraudX Service Account" --description="Service account for Anti-FraudX Cloud deployment"

# 或使用 PowerShell 反引號
gcloud iam service-accounts create anti-fraudx-sa `
  --display-name="Anti-FraudX Service Account" `
  --description="Service account for Anti-FraudX Cloud deployment"
```

### 步驟 1.5：授予服務帳戶角色

```powershell
# 授予 run.admin 角色
gcloud projects add-iam-policy-binding anti-fraudx --member=serviceAccount:anti-fraudx-sa@anti-fraudx.iam.gserviceaccount.com --role=roles/run.admin

# 授予 aiplatform.user 角色
gcloud projects add-iam-policy-binding anti-fraudx --member=serviceAccount:anti-fraudx-sa@anti-fraudx.iam.gserviceaccount.com --role=roles/aiplatform.user

# 授予 datastore.user 角色
gcloud projects add-iam-policy-binding anti-fraudx --member=serviceAccount:anti-fraudx-sa@anti-fraudx.iam.gserviceaccount.com --role=roles/datastore.user

# 授予 storage.admin 角色
gcloud projects add-iam-policy-binding anti-fraudx --member=serviceAccount:anti-fraudx-sa@anti-fraudx.iam.gserviceaccount.com --role=roles/storage.admin
```

### 步驟 1.6：創建服務帳戶密鑰

```powershell
# 方法 1：使用完整路徑（推薦）
gcloud iam service-accounts keys create "C:\Users\andy1\anti-fraudx-key.json" --iam-account=anti-fraudx-sa@anti-fraudx.iam.gserviceaccount.com

# 方法 2：先展開變量
$keyPath = "$env:USERPROFILE\anti-fraudx-key.json"
gcloud iam service-accounts keys create $keyPath --iam-account=anti-fraudx-sa@anti-fraudx.iam.gserviceaccount.com

# 方法 3：使用 ~ 符號
gcloud iam service-accounts keys create "~/anti-fraudx-key.json" --iam-account=anti-fraudx-sa@anti-fraudx.iam.gserviceaccount.com

# 設置認證環境變量（使用雙反斜杠或正斜杠）
$env:GOOGLE_APPLICATION_CREDENTIALS = "C:\\Users\\andy1\\anti-fraudx-key.json"
# 或
$env:GOOGLE_APPLICATION_CREDENTIALS = "C:/Users/andy1/anti-fraudx-key.json"


# 驗證認證
gcloud auth application-default print-access-token
```

### 步驟 1.7：配置 Artifact Registry

```powershell
# 創建 Docker 倉庫
gcloud artifacts repositories create anti-fraudx-repo --repository-format=docker --location=us-central1 --description="Docker repository for Anti-FraudX"

# 配置 Docker 認證
gcloud auth configure-docker us-central1-docker.pkg.dev

# 驗證倉庫
gcloud artifacts repositories list
```

### 步驟 1.8：創建 Firestore 數據庫

```powershell
# 創建 Firestore 數據庫
gcloud firestore databases create --database=anti-fraudx-db --location=us-central1 --type=firestore-native

# 驗證數據庫創建
gcloud firestore databases list
```

### 步驟 1.9：創建 Cloud Storage 存儲桶

```powershell
# 創建存儲桶
gsutil mb -l us-central1 gs://anti-fraudx-storage

# 設置存儲桶權限
gsutil iam ch serviceAccount:anti-fraudx-sa@anti-fraudx.iam.gserviceaccount.com:objectAdmin gs://anti-fraudx-storage

# 驗證存儲桶
gsutil ls
```

---

## 第二階段：代碼遷移 - Windows PowerShell 版本

### 步驟 2.1：創建環境配置文件

#### 創建 `.env.local`

```powershell
# 進入 backend 目錄
cd backend

# 創建 .env.local 文件
@"
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
"@ | Out-File -Encoding UTF8 .env.local
```

#### 創建 `.env.cloud`

```powershell
# 創建 .env.cloud 文件
@"
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
"@ | Out-File -Encoding UTF8 .env.cloud
```

### 步驟 2.2：驗證 Vertex AI LLM 模塊

```powershell
# 檢查文件是否存在
Test-Path llms/vertex_ai_llm.py

# 如果不存在，需要創建
```

### 步驟 2.3：驗證 LLM Factory

```powershell
# 驗證 LLM Factory 支持 Cloud 部署
Select-String -Path llms/llm_factory.py -Pattern "DEPLOYMENT_ENV"
Select-String -Path llms/llm_factory.py -Pattern "vertex_ai"
```

### 步驟 2.4：本地測試 Vertex AI 連接

```powershell
# 設置認證（使用雙反斜杠或正斜杠）
$env:GOOGLE_APPLICATION_CREDENTIALS = "C:\\Users\\andy1\\anti-fraudx-key.json"
# 或
$env:GOOGLE_APPLICATION_CREDENTIALS = "C:/Users/andy1/anti-fraudx-key.json"

# 設置環境變量
$env:DEPLOYMENT_ENV = "cloud"
$env:GCP_PROJECT_ID = "anti-fraudx"
$env:VERTEX_AI_MODEL = "gemini-3.1-flash-lite-preview"

# 運行測試腳本
python tests/test_vertex_ai_gemini.py
```

---

## 第三階段：容器化 - Windows PowerShell 版本

### 步驟 3.1：構建容器鏡像

```powershell
# 設置環境變量
$PROJECT_ID = "anti-fraudx"
$REGION = "us-central1"
$IMAGE_NAME = "anti-fraudx-backend"
$IMAGE_TAG = "latest"
$IMAGE_URL = "$REGION-docker.pkg.dev/$PROJECT_ID/anti-fraudx-repo/$IMAGE_NAME`:$IMAGE_TAG"

# 構建鏡像
docker build -f Dockerfile.cloud -t $IMAGE_URL .

# 驗證鏡像
docker images | Select-String anti-fraudx-backend
```

### 步驟 3.2：推送到 Artifact Registry

```powershell
# 配置 Docker 認證
gcloud auth configure-docker us-central1-docker.pkg.dev

# 推送鏡像
docker push $IMAGE_URL

# 驗證推送
gcloud artifacts docker images list us-central1-docker.pkg.dev/$PROJECT_ID/anti-fraudx-repo
```

### 步驟 3.3：本地測試容器

```powershell
# 運行容器（使用正斜杠避免轉義問題）
docker run -it `
  -e DEPLOYMENT_ENV=cloud `
  -e GCP_PROJECT_ID=$PROJECT_ID `
  -e GOOGLE_APPLICATION_CREDENTIALS=/app/key.json `
  -v "C:/Users/andy1/anti-fraudx-key.json:/app/key.json" `
  -p 8080:8080 `
  $IMAGE_URL

# 在另一個 PowerShell 窗口測試健康檢查
curl http://localhost:8080/health
```

---

## 第四階段：後端部署 - Windows PowerShell 版本

### 步驟 4.1：部署到 Cloud Run

```powershell
# 設置環境變量
$PROJECT_ID = "anti-fraudx"
$REGION = "us-central1"
$SERVICE_NAME = "anti-fraudx-backend"
$IMAGE_NAME = "anti-fraudx-backend"
$IMAGE_TAG = "latest"
$IMAGE_URL = "$REGION-docker.pkg.dev/$PROJECT_ID/anti-fraudx-repo/$IMAGE_NAME`:$IMAGE_TAG"

# 部署到 Cloud Run（使用反引號分行）
gcloud run deploy $SERVICE_NAME `
  --image $IMAGE_URL `
  --platform managed `
  --region $REGION `
  --memory 512Mi `
  --cpu 1 `
  --timeout 3600 `
  --max-instances 10 `
  --min-instances 0 `
  --allow-unauthenticated `
  --set-env-vars DEPLOYMENT_ENV=cloud,GCP_PROJECT_ID=$PROJECT_ID,VERTEX_AI_MODEL=gemini-2.5-flash-lite,GCP_LOCATION=$REGION

# 獲取服務 URL
gcloud run services describe $SERVICE_NAME --region $REGION --format='value(status.url)'
```

### 步驟 4.2：配置 IAM 權限

```powershell
# 授予 Firestore 訪問權限
gcloud projects add-iam-policy-binding $PROJECT_ID --member=serviceAccount:$SERVICE_NAME@$PROJECT_ID.iam.gserviceaccount.com --role=roles/datastore.user

# 授予 Cloud Storage 訪問權限
gcloud projects add-iam-policy-binding $PROJECT_ID --member=serviceAccount:$SERVICE_NAME@$PROJECT_ID.iam.gserviceaccount.com --role=roles/storage.objectAdmin

# 授予 Vertex AI 訪問權限
gcloud projects add-iam-policy-binding $PROJECT_ID --member=serviceAccount:$SERVICE_NAME@$PROJECT_ID.iam.gserviceaccount.com --role=roles/aiplatform.user
```

### 步驟 4.3：測試後端 API

```powershell
# 獲取服務 URL
$SERVICE_URL = gcloud run services describe $SERVICE_NAME --region $REGION --format='value(status.url)'

# 測試健康檢查
curl $SERVICE_URL/health

# 測試 API 端點
curl $SERVICE_URL/test/json
```

---

## 快速參考 - Windows PowerShell 常用命令

### 環境變量設置

```powershell
# 設置環境變量（使用雙反斜杠或正斜杠）
$env:PROJECT_ID = "anti-fraudx"
$env:REGION = "us-central1"
$env:SERVICE_NAME = "anti-fraudx-backend"
$env:GOOGLE_APPLICATION_CREDENTIALS = "C:\\Users\\andy1\\anti-fraudx-key.json"
# 或
$env:GOOGLE_APPLICATION_CREDENTIALS = "C:/Users/andy1/anti-fraudx-key.json"

# 查看環境變量
$env:PROJECT_ID
$env:GOOGLE_APPLICATION_CREDENTIALS
```

### 文件操作

```powershell
# 創建文件
@"
內容
"@ | Out-File -Encoding UTF8 filename.txt

# 讀取文件
Get-Content filename.txt

# 檢查文件是否存在
Test-Path filename.txt
```

### gcloud 命令

```powershell
# 單行命令（推薦用於 Windows）
gcloud services enable run.googleapis.com aiplatform.googleapis.com

# 使用反引號續行
gcloud services enable `
  run.googleapis.com `
  aiplatform.googleapis.com

# 使用變量
gcloud run deploy $SERVICE_NAME --image $IMAGE_URL
```

---

## ⚠️ Windows PowerShell 注意事項

1. **反斜杠 `\` 是轉義字符** - 在字符串中需要使用雙反斜杠 `\\` 或正斜杠 `/`
2. **外部程序的變量展開** - gcloud 等外部程序可能無法正確展開 `$env:VAR`，建議使用完整路徑
3. **反引號 `` ` `` 用於續行** - 在 PowerShell 中用反引號代替 bash 的反斜杠
4. **引號** - 使用雙引號 `"` 展開變量，單引號 `'` 不展開

### 常見錯誤

❌ 錯誤：
```powershell
$env:GOOGLE_APPLICATION_CREDENTIALS = "C:\Users\andy1\anti-fraudx-key.json"
# 錯誤：\U 和 \a 被當作轉義序列
```

✅ 正確：
```powershell
# 方法 1：使用雙反斜杠
$env:GOOGLE_APPLICATION_CREDENTIALS = "C:\\Users\\andy1\\anti-fraudx-key.json"

# 方法 2：使用正斜杠（推薦）
$env:GOOGLE_APPLICATION_CREDENTIALS = "C:/Users/andy1/anti-fraudx-key.json"

# 方法 3：使用原始字符串
$env:GOOGLE_APPLICATION_CREDENTIALS = @"
C:\Users\andy1\anti-fraudx-key.json
"@
```

---

## 推薦方案

**如果你經常使用 bash 命令，建議安裝以下之一：**

1. **Git Bash** - 輕量級，支持 bash 命令
2. **WSL (Windows Subsystem for Linux)** - 完整的 Linux 環境
3. **Windows Terminal** - 支持多個 shell

這樣你就可以直接使用原始的 bash 命令，無需修改。

---

**文檔版本**: v1.0
**最後更新**: 2026-03-15
**狀態**: 準備就緒

