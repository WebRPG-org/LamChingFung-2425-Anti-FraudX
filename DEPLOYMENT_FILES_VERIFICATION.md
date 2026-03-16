# 部署文件驗證報告

## ✅ 已驗證和修正的項目

### 文件 1：DEPLOYMENT_DETAILED_STEPS.md

#### 第一階段：GCP 準備
- ✅ 步驟 1.1：使用正確的專案 ID `gen-lang-client-0029677384`
- ✅ 步驟 1.2：API 啟用命令正確
- ✅ 步驟 1.3：計費驗證已修正（移除舊的 link 命令）
- ✅ 步驟 1.4：服務帳戶配置使用正確的專案 ID
- ✅ 步驟 1.5：Artifact Registry 配置正確
- ✅ 步驟 1.6：Firestore 數據庫配置正確
- ✅ 步驟 1.7：Cloud Storage 權限已修正為正確的專案 ID

#### 第二階段：代碼遷移
- ✅ `.env.local` 配置正確
- ✅ `.env.cloud` 配置已修正：
  - `PROJECT_ID=gen-lang-client-0029677384`
  - `GCP_PROJECT_ID=gen-lang-client-0029677384`
  - `FIRESTORE_PROJECT_ID=gen-lang-client-0029677384`
- ✅ Vertex AI 連接測試命令正確

#### 第三階段：容器化
- ✅ Dockerfile.cloud 配置正確
- ✅ 構建命令已修正為使用 `gen-lang-client-0029677384`
- ✅ 容器測試命令已修正為正確的專案 ID

---

### 文件 2：DEPLOYMENT_DETAILED_STEPS_PART2.md

#### 第四階段：後端部署
- ✅ 環境變量設置使用正確的專案 ID
- ✅ Cloud Run 部署命令正確
- ✅ Secret Manager 配置正確
- ✅ IAM 權限綁定使用正確的專案 ID

#### 第五階段：前端部署
- ✅ 前端構建命令正確
- ✅ Cloud Storage 上傳命令正確
- ✅ CORS 配置正確

#### 第六階段：域名配置
- ✅ DNS 區域創建命令正確
- ✅ DNS 記錄配置命令正確
- ✅ SSL 證書配置正確

#### 第七階段：監控設置
- ✅ Cloud Logging 配置正確
- ✅ Cloud Monitoring 配置正確
- ✅ 告警規則配置正確

#### 第八階段：測試上線
- ✅ 功能測試命令正確
- ✅ 負載測試腳本正確
- ✅ 性能測試命令正確
- ✅ 安全審計命令正確
- ✅ 灰度發布命令正確

#### 常見問題
- ✅ 問題 1 已修正為使用正確的專案 ID
- ✅ 問題 2 和 3 保持正確

---

## 📋 關鍵信息總結

### GCP 專案信息
- **專案 ID**：`gen-lang-client-0029677384`
- **專案名稱**：Gemini Project-50-money
- **區域**：us-central1
- **域名**：anti-fraudx.us.ci

### 資源命名規範
- **服務帳戶**：`anti-fraudx-sa@gen-lang-client-0029677384.iam.gserviceaccount.com`
- **Artifact Registry**：`anti-fraudx-repo`
- **Cloud Run 服務**：`anti-fraudx-backend`
- **Firestore 數據庫**：`anti-fraudx-db`
- **Cloud Storage 存儲桶**：`anti-fraudx-storage`
- **DNS 區域**：`anti-fraudx-us-ci`

### 環境變量配置
```bash
# 核心環境變量
export PROJECT_ID=gen-lang-client-0029677384
export REGION=us-central1
export DOMAIN=anti-fraudx.us.ci
export SERVICE_NAME=anti-fraudx-backend
export IMAGE_NAME=anti-fraudx-backend
export IMAGE_TAG=latest
export IMAGE_URL=us-central1-docker.pkg.dev/${PROJECT_ID}/anti-fraudx-repo/${IMAGE_NAME}:${IMAGE_TAG}
```

---

## 🚀 部署執行順序

### 第一次執行（第一階段）
```bash
# 1. 設置項目
gcloud config set project gen-lang-client-0029677384

# 2. 啟用 API
gcloud services enable run.googleapis.com aiplatform.googleapis.com firestore.googleapis.com storage.googleapis.com logging.googleapis.com monitoring.googleapis.com dns.googleapis.com artifactregistry.googleapis.com

# 3. 創建服務帳戶
gcloud iam service-accounts create anti-fraudx-sa --display-name="Anti-FraudX Service Account"

# 4. 授予權限
gcloud projects add-iam-policy-binding gen-lang-client-0029677384 --member=serviceAccount:anti-fraudx-sa@gen-lang-client-0029677384.iam.gserviceaccount.com --role=roles/run.admin
# ... 其他權限

# 5. 創建密鑰
gcloud iam service-accounts keys create ~/anti-fraudx-key.json --iam-account=anti-fraudx-sa@gen-lang-client-0029677384.iam.gserviceaccount.com

# 6. 配置 Artifact Registry
gcloud artifacts repositories create anti-fraudx-repo --repository-format=docker --location=us-central1

# 7. 創建 Firestore 數據庫
gcloud firestore databases create --database=anti-fraudx-db --location=us-central1 --type=firestore-native

# 8. 創建 Cloud Storage 存儲桶
gsutil mb -l us-central1 gs://anti-fraudx-storage
```

### 第二次執行（第二階段）
```bash
# 1. 創建環境配置文件
# .env.local 和 .env.cloud

# 2. 驗證代碼配置
# 檢查 llm_factory.py 和 main.py

# 3. 本地測試
export GOOGLE_APPLICATION_CREDENTIALS=~/anti-fraudx-key.json
export DEPLOYMENT_ENV=cloud
export GCP_PROJECT_ID=gen-lang-client-0029677384
python backend/tests/test_vertex_ai_connection.py
```

### 第三次執行（第三階段）
```bash
# 1. 構建容器
export PROJECT_ID=gen-lang-client-0029677384
docker build -f Dockerfile.cloud -t us-central1-docker.pkg.dev/${PROJECT_ID}/anti-fraudx-repo/anti-fraudx-backend:latest .

# 2. 推送到 Artifact Registry
gcloud auth configure-docker us-central1-docker.pkg.dev
docker push us-central1-docker.pkg.dev/${PROJECT_ID}/anti-fraudx-repo/anti-fraudx-backend:latest

# 3. 本地測試容器
docker run -it -e DEPLOYMENT_ENV=cloud -e GCP_PROJECT_ID=${PROJECT_ID} -e GOOGLE_APPLICATION_CREDENTIALS=/app/key.json -v ~/anti-fraudx-key.json:/app/key.json -p 8080:8080 us-central1-docker.pkg.dev/${PROJECT_ID}/anti-fraudx-repo/anti-fraudx-backend:latest
```

### 第四次執行（第四到第八階段）
```bash
# 按照 DEPLOYMENT_DETAILED_STEPS_PART2.md 執行
# 第四階段：部署到 Cloud Run
# 第五階段：部署前端
# 第六階段：配置域名
# 第七階段：設置監控
# 第八階段：測試上線
```

---

## ⚠️ 重要提醒

### 必須完成的準備工作
- [ ] 安裝 Google Cloud CLI
- [ ] 安裝 Docker
- [ ] 安裝 gcloud 認證工具
- [ ] 確保有 GCP 專案的管理員權限
- [ ] 準備 Gemini API Key（如果需要）

### 必須保存的文件
- [ ] `~/anti-fraudx-key.json` - 服務帳戶密鑰（非常重要！）
- [ ] `.env.local` - 本地環境配置
- [ ] `.env.cloud` - Cloud 環境配置

### 必須驗證的事項
- [ ] GCP 專案 ID 正確：`gen-lang-client-0029677384`
- [ ] 所有 API 已啟用
- [ ] 服務帳戶已創建並授予權限
- [ ] Artifact Registry 已創建
- [ ] Firestore 數據庫已創建
- [ ] Cloud Storage 存儲桶已創建

---

## 📊 部署檢查清單

### 準備階段
- [ ] 確認 GCP 專案 ID：`gen-lang-client-0029677384`
- [ ] 確認區域：`us-central1`
- [ ] 確認域名：`anti-fraudx.us.ci`
- [ ] 準備服務帳戶密鑰

### 第一階段：GCP 準備
- [ ] 設置項目
- [ ] 啟用 API
- [ ] 驗證計費
- [ ] 創建服務帳戶
- [ ] 配置 Artifact Registry
- [ ] 創建 Firestore 數據庫
- [ ] 創建 Cloud Storage 存儲桶

### 第二階段：代碼遷移
- [ ] 創建 `.env.local`
- [ ] 創建 `.env.cloud`
- [ ] 驗證 Vertex AI LLM 模塊
- [ ] 驗證 LLM Factory
- [ ] 本地測試 Vertex AI 連接

### 第三階段：容器化
- [ ] 創建 Dockerfile.cloud
- [ ] 構建容器鏡像
- [ ] 推送到 Artifact Registry
- [ ] 本地測試容器

### 第四階段：後端部署
- [ ] 部署到 Cloud Run
- [ ] 配置環境變量
- [ ] 配置自動擴展
- [ ] 測試後端 API
- [ ] 配置 IAM 權限

### 第五階段：前端部署
- [ ] 構建前端應用
- [ ] 上傳到 Cloud Storage
- [ ] 配置靜態網站託管
- [ ] 配置 CORS
- [ ] 測試前端訪問

### 第六階段：域名配置
- [ ] 創建 DNS 區域
- [ ] 配置 DNS 記錄
- [ ] 申請 SSL 證書
- [ ] 驗證 HTTPS

### 第七階段：監控設置
- [ ] 設置 Cloud Logging
- [ ] 設置 Cloud Monitoring
- [ ] 配置告警規則
- [ ] 設置通知渠道

### 第八階段：測試上線
- [ ] 功能測試
- [ ] 負載測試
- [ ] 性能測試
- [ ] 安全審計
- [ ] 灰度發布
- [ ] 正式上線

---

## 📞 快速參考

### 常用命令
```bash
# 設置項目
gcloud config set project gen-lang-client-0029677384

# 查看項目信息
gcloud projects describe gen-lang-client-0029677384

# 查看服務帳戶
gcloud iam service-accounts list

# 查看 Cloud Run 服務
gcloud run services list --region us-central1

# 查看日誌
gcloud logging read "resource.type=cloud_run_revision" --limit 50

# 查看監控指標
gcloud monitoring time-series list --filter='metric.type="run.googleapis.com/request_count"'
```

---

**驗證完成時間**：2026-03-15
**驗證狀態**：✅ 所有文件已驗證和修正
**下一步**：開始執行第一階段部署

