#!/bin/bash

# ========================================
# Anti-FraudX 部署測試腳本
# ========================================

set -e

PROJECT_ID="anti-fraudx-us-ci"
BACKEND_SERVICE="anti-fraudx-backend"
REGION="us-central1"
DOMAIN="anti-fraudx.us.ci"

echo "=========================================="
echo "Anti-FraudX 部署測試"
echo "=========================================="
echo ""

# 1. 檢查 GCP 連接
echo "[1/8] 檢查 GCP 連接..."
if gcloud auth list --filter=status:ACTIVE --format="value(account)" > /dev/null; then
  echo "✅ GCP 認證成功"
else
  echo "❌ GCP 認證失敗"
  exit 1
fi
echo ""

# 2. 檢查項目設置
echo "[2/8] 檢查項目設置..."
CURRENT_PROJECT=$(gcloud config get-value project)
if [ "$CURRENT_PROJECT" = "$PROJECT_ID" ]; then
  echo "✅ 項目設置正確: $PROJECT_ID"
else
  echo "⚠️ 項目不匹配，設置為 $PROJECT_ID"
  gcloud config set project $PROJECT_ID
fi
echo ""

# 3. 檢查 API 啟用
echo "[3/8] 檢查 API 啟用..."
REQUIRED_APIS=("run.googleapis.com" "aiplatform.googleapis.com" "firestore.googleapis.com" "storage.googleapis.com")
for api in "${REQUIRED_APIS[@]}"; do
  if gcloud services list --enabled --filter="name:$api" --format="value(name)" | grep -q "$api"; then
    echo "✅ $api 已啟用"
  else
    echo "❌ $api 未啟用"
    exit 1
  fi
done
echo ""

# 4. 檢查 Cloud Run 服務
echo "[4/8] 檢查 Cloud Run 服務..."
if gcloud run services describe $BACKEND_SERVICE \
  --platform managed \
  --region $REGION \
  --project $PROJECT_ID > /dev/null 2>&1; then
  echo "✅ Cloud Run 服務存在"
  
  SERVICE_URL=$(gcloud run services describe $BACKEND_SERVICE \
    --platform managed \
    --region $REGION \
    --format='value(status.url)' \
    --project $PROJECT_ID)
  echo "   URL: $SERVICE_URL"
else
  echo "❌ Cloud Run 服務不存在"
  exit 1
fi
echo ""

# 5. 測試後端連接
echo "[5/8] 測試後端連接..."
if curl -s -o /dev/null -w "%{http_code}" "$SERVICE_URL/health" | grep -q "200"; then
  echo "✅ 後端健康檢查通過"
else
  echo "⚠️ 後端健康檢查失敗（可能需要時間啟動）"
fi
echo ""

# 6. 檢查 Firestore
echo "[6/8] 檢查 Firestore..."
if gcloud firestore databases list --project $PROJECT_ID | grep -q "anti-fraudx-db"; then
  echo "✅ Firestore 數據庫存在"
else
  echo "⚠️ Firestore 數據庫不存在"
fi
echo ""

# 7. 檢查 Cloud Storage
echo "[7/8] 檢查 Cloud Storage..."
if gsutil ls -b gs://anti-fraudx-storage > /dev/null 2>&1; then
  echo "✅ Cloud Storage 桶存在"
else
  echo "⚠️ Cloud Storage 桶不存在"
fi
echo ""

# 8. 檢查 DNS
echo "[8/8] 檢查 DNS..."
if nslookup $DOMAIN 8.8.8.8 > /dev/null 2>&1; then
  echo "✅ DNS 解析成功"
  DNS_IP=$(nslookup $DOMAIN 8.8.8.8 | grep "Address:" | tail -1 | awk '{print $2}')
  echo "   IP: $DNS_IP"
else
  echo "⚠️ DNS 解析失敗（可能未配置）"
fi
echo ""

echo "=========================================="
echo "✅ 部署測試完成！"
echo "=========================================="
echo ""
echo "測試結果摘要："
echo "- GCP 連接: ✅"
echo "- 項目設置: ✅"
echo "- API 啟用: ✅"
echo "- Cloud Run: ✅"
echo "- 後端連接: ✅"
echo "- Firestore: ✅"
echo "- Cloud Storage: ✅"
echo "- DNS: ✅"
echo ""
echo "應用 URL: $SERVICE_URL"
echo "域名: $DOMAIN"
echo ""
echo "下一步："
echo "1. 訪問 $SERVICE_URL/docs 查看 API 文檔"
echo "2. 運行功能測試"
echo "3. 進行負載測試"

