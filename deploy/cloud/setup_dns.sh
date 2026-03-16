#!/bin/bash

# ========================================
# Anti-FraudX DNS 配置腳本
# ========================================

set -e

PROJECT_ID="anti-fraudx-us-ci"
DOMAIN="anti-fraudx.us.ci"
DNS_ZONE="anti-fraudx-us-ci"
BACKEND_SERVICE="anti-fraudx-backend"
REGION="us-central1"

echo "=========================================="
echo "Anti-FraudX DNS 配置"
echo "=========================================="
echo ""

# 1. 獲取 Cloud Run 服務 URL
echo "[1/4] 獲取 Cloud Run 服務 URL..."
SERVICE_URL=$(gcloud run services describe $BACKEND_SERVICE \
  --platform managed \
  --region $REGION \
  --format='value(status.url)' \
  --project $PROJECT_ID)

echo "✅ 服務 URL: $SERVICE_URL"
echo ""

# 2. 提取主機名
echo "[2/4] 提取主機名..."
SERVICE_HOST=$(echo $SERVICE_URL | sed 's|https://||' | sed 's|/||')
echo "✅ 服務主機: $SERVICE_HOST"
echo ""

# 3. 創建 DNS 記錄
echo "[3/4] 創建 DNS 記錄..."

# 獲取 DNS 區域的名稱服務器
NAMESERVERS=$(gcloud dns managed-zones describe $DNS_ZONE \
  --project $PROJECT_ID \
  --format='value(nameServers[0:4])')

echo "✅ 名稱服務器:"
echo "$NAMESERVERS"
echo ""

# 創建 CNAME 記錄
gcloud dns record-sets create $DOMAIN \
  --rrdatas=$SERVICE_HOST \
  --ttl=300 \
  --type=CNAME \
  --zone=$DNS_ZONE \
  --project $PROJECT_ID 2>/dev/null || echo "⚠️ 記錄已存在或更新"

echo "✅ DNS 記錄已配置"
echo ""

# 4. 驗證 DNS
echo "[4/4] 驗證 DNS..."
echo "等待 DNS 傳播（可能需要幾分鐘）..."

# 嘗試解析域名
for i in {1..10}; do
  if nslookup $DOMAIN 8.8.8.8 > /dev/null 2>&1; then
    echo "✅ DNS 解析成功！"
    nslookup $DOMAIN 8.8.8.8
    break
  else
    echo "⏳ 等待中... ($i/10)"
    sleep 10
  fi
done

echo ""
echo "=========================================="
echo "✅ DNS 配置完成！"
echo "=========================================="
echo ""
echo "域名: $DOMAIN"
echo "服務 URL: $SERVICE_URL"
echo ""
echo "下一步："
echo "1. 更新域名註冊商的名稱服務器指向："
for ns in $NAMESERVERS; do
  echo "   - $ns"
done
echo "2. 等待 DNS 傳播（通常 24-48 小時）"
echo "3. 訪問 https://$DOMAIN 測試應用"
echo ""
echo "提示："
echo "- 可以使用 'dig $DOMAIN' 檢查 DNS 狀態"
echo "- 可以使用 'curl -I https://$DOMAIN' 測試連接"

