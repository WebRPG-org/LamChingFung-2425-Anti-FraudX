#!/bin/bash

# ========================================
# Anti-FraudX 計費和告警設置
# ========================================

set -e

PROJECT_ID="anti-fraudx-us-ci"
BUDGET_AMOUNT="50"  # 美元
ALERT_THRESHOLD="100"  # 百分比

echo "=========================================="
echo "Anti-FraudX 計費和告警設置"
echo "=========================================="
echo ""

# 1. 獲取計費帳戶
echo "[1/3] 獲取計費帳戶..."
BILLING_ACCOUNT=$(gcloud billing accounts list --format='value(name)' | head -1)

if [ -z "$BILLING_ACCOUNT" ]; then
    echo "❌ 未找到計費帳戶"
    echo "請先在 Google Cloud Console 設置計費帳戶"
    exit 1
fi

echo "✅ 計費帳戶: $BILLING_ACCOUNT"
echo ""

# 2. 將計費帳戶關聯到項目
echo "[2/3] 將計費帳戶關聯到項目..."
gcloud billing projects link $PROJECT_ID \
  --billing-account=$BILLING_ACCOUNT
echo "✅ 計費帳戶已關聯"
echo ""

# 3. 創建預算告警
echo "[3/3] 創建預算告警..."
gcloud billing budgets create \
  --billing-account=$BILLING_ACCOUNT \
  --display-name="Anti-FraudX Budget" \
  --budget-amount=$BUDGET_AMOUNT \
  --threshold-rule=percent=$ALERT_THRESHOLD \
  --threshold-rule=percent=50 \
  --threshold-rule=percent=90 \
  2>/dev/null || echo "預算已存在"

echo "✅ 預算告警設置完成"
echo ""

echo "=========================================="
echo "✅ 計費和告警設置完成！"
echo "=========================================="
echo ""
echo "預算設置："
echo "  - 月度預算: $BUDGET_AMOUNT USD"
echo "  - 告警閾值: $ALERT_THRESHOLD%"
echo ""
echo "提示："
echo "1. 定期檢查 Google Cloud Console 的計費頁面"
echo "2. 設置郵件通知以接收預算告警"
echo "3. 監控 Vertex AI 和 Cloud Run 的成本"

