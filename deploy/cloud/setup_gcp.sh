#!/bin/bash

# ========================================
# Anti-FraudX Google Cloud 初始化腳本
# ========================================

set -e

PROJECT_ID="anti-fraudx-us-ci"
PROJECT_NAME="Anti-FraudX"
REGION="us-central1"
DOMAIN="anti-fraudx.us.ci"
SERVICE_ACCOUNT="anti-fraudx-sa"

echo "=========================================="
echo "Anti-FraudX Google Cloud 初始化"
echo "=========================================="
echo ""

# 1. 創建項目
echo "[1/7] 創建 Google Cloud 項目..."
gcloud projects create $PROJECT_ID --name="$PROJECT_NAME" 2>/dev/null || echo "項目已存在"
gcloud config set project $PROJECT_ID
echo "✅ 項目設置完成"
echo ""

# 2. 啟用 API
echo "[2/7] 啟用必要的 API..."
gcloud services enable \
  run.googleapis.com \
  aiplatform.googleapis.com \
  firestore.googleapis.com \
  storage.googleapis.com \
  logging.googleapis.com \
  monitoring.googleapis.com \
  dns.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  iam.googleapis.com
echo "✅ API 啟用完成"
echo ""

# 3. 創建服務帳戶
echo "[3/7] 創建服務帳戶..."
gcloud iam service-accounts create $SERVICE_ACCOUNT \
  --display-name="Anti-FraudX Service Account" 2>/dev/null || echo "服務帳戶已存在"
echo "✅ 服務帳戶創建完成"
echo ""

# 4. 授予權限
echo "[4/7] 授予 IAM 權限..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member=serviceAccount:${SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com \
  --role=roles/aiplatform.user \
  --quiet 2>/dev/null || echo "權限已存在"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member=serviceAccount:${SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com \
  --role=roles/datastore.user \
  --quiet 2>/dev/null || echo "權限已存在"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member=serviceAccount:${SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com \
  --role=roles/storage.objectAdmin \
  --quiet 2>/dev/null || echo "權限已存在"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member=serviceAccount:${SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com \
  --role=roles/logging.logWriter \
  --quiet 2>/dev/null || echo "權限已存在"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member=serviceAccount:${SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com \
  --role=roles/monitoring.metricWriter \
  --quiet 2>/dev/null || echo "權限已存在"

echo "✅ IAM 權限設置完成"
echo ""

# 5. 創建 Firestore 數據庫
echo "[5/7] 創建 Firestore 數據庫..."
gcloud firestore databases create \
  --location=$REGION \
  --type=firestore-native 2>/dev/null || echo "Firestore 數據庫已存在"
echo "✅ Firestore 數據庫創建完成"
echo ""

# 6. 創建 Cloud Storage 桶
echo "[6/7] 創建 Cloud Storage 桶..."
gsutil mb -l $REGION gs://anti-fraudx-storage 2>/dev/null || echo "Storage 桶已存在"
echo "✅ Cloud Storage 桶創建完成"
echo ""

# 7. 創建 Cloud DNS 區域
echo "[7/7] 創建 Cloud DNS 區域..."
gcloud dns managed-zones create anti-fraudx-us-ci \
  --dns-name=$DOMAIN \
  --description="Anti-FraudX DNS Zone" 2>/dev/null || echo "DNS 區域已存在"
echo "✅ Cloud DNS 區域創建完成"
echo ""

echo "=========================================="
echo "✅ Anti-FraudX GCP 初始化完成！"
echo "=========================================="
echo ""
echo "下一步："
echo "1. 配置 DNS 記錄（指向 Cloud Run）"
echo "2. 部署後端到 Cloud Run"
echo "3. 部署前端到 Cloud Storage"
echo ""
echo "運行以下命令部署："
echo "  ./deploy/cloud/deploy_to_cloud.sh"

