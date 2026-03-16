#!/bin/bash

# ========================================
# Anti-FraudX Cloud Run 部署腳本
# ========================================

set -e

PROJECT_ID="anti-fraudx-us-ci"
BACKEND_SERVICE="anti-fraudx-backend"
REGION="us-central1"
IMAGE="gcr.io/$PROJECT_ID/$BACKEND_SERVICE"

echo "=========================================="
echo "Anti-FraudX Cloud Run 部署"
echo "=========================================="
echo ""

# 1. 設置項目
echo "[1/5] 設置 Google Cloud 項目..."
gcloud config set project $PROJECT_ID
echo "✅ 項目設置完成"
echo ""

# 2. 構建容器
echo "[2/5] 構建容器鏡像..."
gcloud builds submit \
  --tag $IMAGE \
  --timeout=1800s \
  --machine-type=N1_HIGHCPU_8
echo "✅ 容器構建完成"
echo ""

# 3. 部署到 Cloud Run
echo "[3/5] 部署到 Cloud Run..."
gcloud run deploy $BACKEND_SERVICE \
  --image $IMAGE \
  --platform managed \
  --region $REGION \
  --memory 512Mi \
  --cpu 1 \
  --timeout 3600 \
  --max-instances 10 \
  --min-instances 0 \
  --allow-unauthenticated \
  --set-env-vars="DEPLOYMENT_ENV=cloud,PROJECT_ID=$PROJECT_ID,GCP_PROJECT_ID=$PROJECT_ID,GCP_LOCATION=$REGION,USE_VERTEX_AI=true,VERTEX_AI_MODEL=gemini-3.1-flash,DATABASE_TYPE=firestore,FIRESTORE_PROJECT_ID=$PROJECT_ID,FIRESTORE_DATABASE=anti-fraudx-db,STORAGE_TYPE=gcs,CLOUD_STORAGE_BUCKET=anti-fraudx-storage,CLOUD_RUN_SERVICE=$BACKEND_SERVICE,DOMAIN_NAME=anti-fraudx.us.ci,APP_NAME=Anti-FraudX,APP_VERSION=2.0.0,APP_ENV=production,LOG_LEVEL=info"
echo "✅ Cloud Run 部署完成"
echo ""

# 4. 獲取服務 URL
echo "[4/5] 獲取服務 URL..."
SERVICE_URL=$(gcloud run services describe $BACKEND_SERVICE \
  --platform managed \
  --region $REGION \
  --format='value(status.url)')
echo "✅ 服務 URL: $SERVICE_URL"
echo ""

# 5. 配置 IAM 權限
echo "[5/5] 配置 IAM 權限..."
SERVICE_ACCOUNT=$(gcloud run services describe $BACKEND_SERVICE \
  --platform managed \
  --region $REGION \
  --format='value(spec.template.spec.serviceAccountName)')

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member=serviceAccount:$SERVICE_ACCOUNT \
  --role=roles/aiplatform.user \
  --quiet 2>/dev/null || echo "權限已存在"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member=serviceAccount:$SERVICE_ACCOUNT \
  --role=roles/datastore.user \
  --quiet 2>/dev/null || echo "權限已存在"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member=serviceAccount:$SERVICE_ACCOUNT \
  --role=roles/storage.objectAdmin \
  --quiet 2>/dev/null || echo "權限已存在"

echo "✅ IAM 權限配置完成"
echo ""

# 6. 部署前端到 Cloud Storage
echo "[6/6] 部署前端到 Cloud Storage..."
if [ -d "rpg-platform-v2/dist" ]; then
  gsutil -m cp -r rpg-platform-v2/dist/* gs://anti-fraudx-storage/
  echo "✅ RPG v2 前端已部署"
else
  echo "⚠️ RPG v2 dist 目錄不存在，跳過"
fi

if [ -d "frontend" ]; then
  gsutil -m cp -r frontend/* gs://anti-fraudx-storage/
  echo "✅ 前端已部署"
else
  echo "⚠️ 前端目錄不存在，跳過"
fi

echo ""
echo "=========================================="
echo "✅ Anti-FraudX 完整部署完成！"
echo "=========================================="
echo ""
echo "服務 URL: $SERVICE_URL"
echo "前端 URL: https://anti-fraudx.us.ci"
echo ""
echo "下一步："
echo "1. 配置 DNS 記錄指向 Cloud Run 服務"
echo "2. 配置 Cloud Storage 靜態網站託管"
echo "3. 測試應用"

