# Anti-FraudX 完整部署詳細步驟指南 - 第二部分

## 第四階段：後端部署到 Cloud Run

### 步驟 4.1：部署到 Cloud Run

```bash
# 1. 設置環境變量
export PROJECT_ID=anti-fraudx
export REGION=us-central1
export SERVICE_NAME=anti-fraudx-backend
export IMAGE_NAME=anti-fraudx-backend
export IMAGE_TAG=latest
export IMAGE_URL=us-central1-docker.pkg.dev/${PROJECT_ID}/anti-fraudx-repo/${IMAGE_NAME}:${IMAGE_TAG}

# 2. 部署到 Cloud Run
gcloud run deploy ${SERVICE_NAME} \
  --image ${IMAGE_URL} \
  --platform managed \
  --region ${REGION} \
  --memory 512Mi \
  --cpu 1 \
  --timeout 3600 \
  --max-instances 10 \
  --min-instances 0 \
  --allow-unauthenticated \
  --set-env-vars DEPLOYMENT_ENV=cloud,GCP_PROJECT_ID=${PROJECT_ID},VERTEX_AI_MODEL=gemini-3.1-flash,GCP_LOCATION=${REGION}

# 3. 獲取服務 URL
gcloud run services describe ${SERVICE_NAME} --region ${REGION} --format='value(status.url)'
```

### 步驟 4.2：配置環境變量和密鑰

```bash
# 1. 創建 Secret Manager 中的密鑰（如果需要）
echo -n "your_gemini_api_key" | gcloud secrets create gemini-api-key --data-file=-

# 2. 授予 Cloud Run 服務帳戶訪問密鑰的權限
gcloud secrets add-iam-policy-binding gemini-api-key \
  --member=serviceAccount:anti-fraudx-sa@gen-lang-client-0029677384.iam.gserviceaccount.com \
  --role=roles/secretmanager.secretAccessor

# 3. 更新 Cloud Run 服務以使用密鑰
gcloud run services update ${SERVICE_NAME} \
  --region ${REGION} \
  --set-secrets GEMINI_API_KEY=gemini-api-key:latest
```

### 步驟 4.3：配置自動擴展

```bash
# 1. 設置自動擴展策略
gcloud run services update ${SERVICE_NAME} \
  --region ${REGION} \
  --min-instances 0 \
  --max-instances 10

# 2. 驗證配置
gcloud run services describe ${SERVICE_NAME} --region ${REGION}
```

### 步驟 4.4：測試後端 API

```bash
# 1. 獲取服務 URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region ${REGION} --format='value(status.url)')

# 2. 測試健康檢查
curl ${SERVICE_URL}/health

# 3. 測試 API 端點
curl ${SERVICE_URL}/test/json

# 4. 測試 WebSocket（可選）
# 使用 WebSocket 客戶端測試
```

### 步驟 4.5：配置 IAM 權限

```bash
# 1. 授予 Cloud Run 服務帳戶 Firestore 訪問權限
gcloud projects add-iam-policy-binding anti-fraudx \
  --member=serviceAccount:${SERVICE_NAME}@anti-fraudx.iam.gserviceaccount.com \
  --role=roles/datastore.user

# 2. 授予 Cloud Storage 訪問權限
gcloud projects add-iam-policy-binding anti-fraudx \
  --member=serviceAccount:${SERVICE_NAME}@anti-fraudx.iam.gserviceaccount.com \
  --role=roles/storage.objectAdmin

# 3. 授予 Vertex AI 訪問權限
gcloud projects add-iam-policy-binding anti-fraudx \
  --member=serviceAccount:${SERVICE_NAME}@anti-fraudx.iam.gserviceaccount.com \
  --role=roles/aiplatform.user
```

---

## 第五階段：前端部署

### 步驟 5.1：構建前端應用

```bash
# 1. 進入前端目錄
cd rpg-platform-v2

# 2. 安裝依賴（如果使用 Node.js）
npm install

# 3. 構建生產版本
npm run build

# 4. 驗證構建輸出
ls -la dist/
```

### 步驟 5.2：上傳前端到 Cloud Storage

```bash
# 1. 設置環境變量
export BUCKET_NAME=anti-fraudx-storage
export FRONTEND_DIR=rpg-platform-v2/dist

# 2. 上傳前端文件
gsutil -m cp -r ${FRONTEND_DIR}/* gs://${BUCKET_NAME}/

# 3. 驗證上傳
gsutil ls gs://${BUCKET_NAME}/
```

### 步驟 5.3：配置 Cloud Storage 靜態網站託管

```bash
# 1. 設置默認主頁和錯誤頁面
gsutil web set -m index.html -e 404.html gs://${BUCKET_NAME}

# 2. 配置 CORS 策略
cat > cors.json << 'EOF'
[
  {
    "origin": ["*"],
    "method": ["GET", "HEAD", "DELETE"],
    "responseHeader": ["Content-Type"],
    "maxAgeSeconds": 3600
  }
]
EOF

gsutil cors set cors.json gs://${BUCKET_NAME}

# 3. 驗證配置
gsutil cors get gs://${BUCKET_NAME}
```

### 步驟 5.4：配置 Cloud CDN（可選）

```bash
# 1. 創建後端存儲桶
gcloud compute backend-buckets create anti-fraudx-backend-bucket \
  --gcs-uri-prefix=gs://${BUCKET_NAME} \
  --enable-cdn

# 2. 創建 URL 映射
gcloud compute url-maps create anti-fraudx-url-map \
  --default-backend-bucket=anti-fraudx-backend-bucket

# 3. 創建 HTTPS 代理
gcloud compute target-https-proxies create anti-fraudx-https-proxy \
  --url-map=anti-fraudx-url-map \
  --ssl-certificates=anti-fraudx-ssl-cert

# 4. 創建轉發規則
gcloud compute forwarding-rules create anti-fraudx-forwarding-rule \
  --global \
  --target-https-proxy=anti-fraudx-https-proxy \
  --address=anti-fraudx-ip \
  --ports=443
```

### 步驟 5.5：測試前端訪問

```bash
# 1. 獲取存儲桶 URL
BUCKET_URL=https://storage.googleapis.com/${BUCKET_NAME}

# 2. 測試訪問
curl ${BUCKET_URL}/index.html

# 3. 驗證 CORS
curl -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: GET" \
  -H "Access-Control-Request-Headers: Content-Type" \
  -X OPTIONS ${BUCKET_URL}/
```

---

## 第六階段：域名配置

### 步驟 6.1：創建 Cloud DNS 區域

```bash
# 1. 設置環境變量
export DOMAIN=anti-fraudx.us.ci
export DNS_ZONE=anti-fraudx-us-ci

# 2. 創建 DNS 區域
gcloud dns managed-zones create ${DNS_ZONE} \
  --dns-name=${DOMAIN} \
  --description="DNS zone for Anti-FraudX"

# 3. 獲取 DNS 名稱服務器
gcloud dns managed-zones describe ${DNS_ZONE} --format="value(nameServers[])"
```

### 步驟 6.2：配置 DNS 記錄

```bash
# 1. 獲取 Cloud Run 服務的靜態 IP
SERVICE_URL=$(gcloud run services describe anti-fraudx-backend \
  --region us-central1 \
  --format='value(status.url)')

# 提取 IP（需要手動查詢或使用 nslookup）
# nslookup <service-url>

# 2. 創建 A 記錄（指向 Cloud Run）
gcloud dns record-sets create ${DOMAIN} \
  --rrdatas=<CLOUD_RUN_IP> \
  --ttl=300 \
  --type=A \
  --zone=${DNS_ZONE}

# 3. 創建 CNAME 記錄（指向 Cloud Storage）
gcloud dns record-sets create www.${DOMAIN} \
  --rrdatas=c.storage.googleapis.com \
  --ttl=300 \
  --type=CNAME \
  --zone=${DNS_ZONE}

# 4. 驗證 DNS 記錄
gcloud dns record-sets list --zone=${DNS_ZONE}
```

### 步驟 6.3：申請 SSL 證書

```bash
# 1. 使用 Google-managed SSL 證書
gcloud compute ssl-certificates create anti-fraudx-ssl-cert \
  --domains=${DOMAIN},www.${DOMAIN}

# 2. 驗證證書
gcloud compute ssl-certificates describe anti-fraudx-ssl-cert

# 3. 等待證書驗證（通常需要 15-30 分鐘）
```

### 步驟 6.4：驗證 HTTPS 連接

```bash
# 1. 等待 DNS 傳播（通常 5-30 分鐘）
nslookup ${DOMAIN}

# 2. 測試 HTTPS 連接
curl https://${DOMAIN}/health

# 3. 檢查 SSL 證書
openssl s_client -connect ${DOMAIN}:443
```

---

## 第七階段：監控設置

### 步驟 7.1：設置 Cloud Logging

```bash
# 1. 創建日誌接收器
gcloud logging sinks create anti-fraudx-logs \
  logging.googleapis.com/projects/${PROJECT_ID}/logs/anti-fraudx \
  --log-filter='resource.type="cloud_run_revision" AND resource.labels.service_name="anti-fraudx-backend"'

# 2. 查看日誌
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=anti-fraudx-backend" \
  --limit 50 \
  --format json

# 3. 創建日誌查詢
gcloud logging read "severity=ERROR" --limit 10
```

### 步驟 7.2：設置 Cloud Monitoring

```bash
# 1. 創建監控儀表板
gcloud monitoring dashboards create --config-from-file=- << 'EOF'
{
  "displayName": "Anti-FraudX Dashboard",
  "mosaicLayout": {
    "columns": 12,
    "tiles": [
      {
        "width": 6,
        "height": 4,
        "widget": {
          "title": "Cloud Run 請求數",
          "xyChart": {
            "dataSets": [
              {
                "timeSeriesQuery": {
                  "timeSeriesFilter": {
                    "filter": "metric.type=\"run.googleapis.com/request_count\" resource.type=\"cloud_run_revision\""
                  }
                }
              }
            ]
          }
        }
      },
      {
        "xPos": 6,
        "width": 6,
        "height": 4,
        "widget": {
          "title": "Cloud Run 延遲",
          "xyChart": {
            "dataSets": [
              {
                "timeSeriesQuery": {
                  "timeSeriesFilter": {
                    "filter": "metric.type=\"run.googleapis.com/request_latencies\" resource.type=\"cloud_run_revision\""
                  }
                }
              }
            ]
          }
        }
      }
    ]
  }
}
EOF

# 2. 驗證儀表板
gcloud monitoring dashboards list
```

### 步驟 7.3：配置告警規則

```bash
# 1. 創建高錯誤率告警
gcloud alpha monitoring policies create \
  --notification-channels=<CHANNEL_ID> \
  --display-name="Anti-FraudX High Error Rate" \
  --condition-display-name="Error rate > 5%" \
  --condition-threshold-value=0.05 \
  --condition-threshold-filter='metric.type="run.googleapis.com/request_count" AND metric.labels.response_code_class="5xx"'

# 2. 創建高延遲告警
gcloud alpha monitoring policies create \
  --notification-channels=<CHANNEL_ID> \
  --display-name="Anti-FraudX High Latency" \
  --condition-display-name="Latency > 1000ms" \
  --condition-threshold-value=1000 \
  --condition-threshold-filter='metric.type="run.googleapis.com/request_latencies"'

# 3. 列出所有告警
gcloud alpha monitoring policies list
```

### 步驟 7.4：設置通知渠道

```bash
# 1. 創建郵件通知渠道
gcloud alpha monitoring channels create \
  --display-name="Anti-FraudX Email" \
  --type=email \
  --channel-labels=email_address=your-email@example.com

# 2. 列出通知渠道
gcloud alpha monitoring channels list
```

---

## 第八階段：測試上線

### 步驟 8.1：功能測試

```bash
# 1. 測試健康檢查
curl https://${DOMAIN}/health

# 2. 測試 API 端點
curl https://${DOMAIN}/test/json

# 3. 測試遊戲 API
curl https://${DOMAIN}/api/game/info

# 4. 測試個人對話
curl -X POST https://${DOMAIN}/api/personal-chat/start \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test_user","scam_type":"phishing"}'

# 5. 測試模擬
curl -X POST https://${DOMAIN}/simulation/start \
  -H "Content-Type: application/json" \
  -d '{"scam_type":"phishing"}'
```

### 步驟 8.2：負載測試（30 人並發）

```bash
# 1. 安裝負載測試工具
pip install locust

# 2. 創建負載測試腳本
cat > locustfile.py << 'EOF'
from locust import HttpUser, task, between

class AntifraudxUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def health_check(self):
        self.client.get("/health")
    
    @task
    def test_api(self):
        self.client.get("/test/json")
    
    @task
    def game_info(self):
        self.client.get("/api/game/info")
EOF

# 3. 運行負載測試
locust -f locustfile.py \
  --host=https://${DOMAIN} \
  --users=30 \
  --spawn-rate=5 \
  --run-time=5m

# 4. 查看結果
# 打開 http://localhost:8089
```

### 步驟 8.3：性能基準測試

```bash
# 1. 測試平均響應時間
ab -n 1000 -c 30 https://${DOMAIN}/health

# 2. 測試吞吐量
wrk -t4 -c30 -d30s https://${DOMAIN}/health

# 3. 分析結果
# 應該看到：
# - 平均響應時間 < 500ms
# - 99% 響應時間 < 1000ms
# - 吞吐量 > 100 req/s
```

### 步驟 8.4：安全審計

```bash
# 1. 檢查 HTTPS 配置
curl -I https://${DOMAIN}

# 2. 驗證 SSL 證書
openssl s_client -connect ${DOMAIN}:443 -showcerts

# 3. 檢查安全頭
curl -I https://${DOMAIN} | grep -i "strict-transport-security\|x-content-type-options\|x-frame-options"

# 4. 檢查 CORS 配置
curl -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: GET" \
  -X OPTIONS https://${DOMAIN}
```

### 步驟 8.5：灰度發布

```bash
# 1. 創建新版本
gcloud run deploy anti-fraudx-backend-v2 \
  --image ${IMAGE_URL} \
  --region us-central1 \
  --no-traffic

# 2. 測試新版本
NEW_SERVICE_URL=$(gcloud run services describe anti-fraudx-backend-v2 \
  --region us-central1 \
  --format='value(status.url)')

curl ${NEW_SERVICE_URL}/health

# 3. 逐步遷移流量
gcloud run services update-traffic anti-fraudx-backend \
  --to-revisions anti-fraudx-backend-v1=50,anti-fraudx-backend-v2=50 \
  --region us-central1

# 4. 監控指標
gcloud logging read "resource.type=cloud_run_revision" --limit 100

# 5. 完全遷移
gcloud run services update-traffic anti-fraudx-backend \
  --to-revisions anti-fraudx-backend-v2=100 \
  --region us-central1
```

### 步驟 8.6：正式上線

```bash
# 1. 最終驗證
curl https://${DOMAIN}/health
curl https://${DOMAIN}/test/json

# 2. 檢查日誌
gcloud logging read "resource.type=cloud_run_revision" --limit 50

# 3. 檢查監控指標
gcloud monitoring time-series list \
  --filter='metric.type="run.googleapis.com/request_count"'

# 4. 宣布上線
echo "✅ Anti-FraudX 已成功部署到 https://${DOMAIN}"
```

---

## 📊 部署檢查清單

### 第一階段：GCP 準備
- [ ] 創建 Google Cloud 項目
- [ ] 啟用必要的 API
- [ ] 設置計費和配額告警
- [ ] 創建服務帳戶和密鑰
- [ ] 配置 Artifact Registry
- [ ] 創建 Firestore 數據庫
- [ ] 創建 Cloud Storage 存儲桶

### 第二階段：代碼遷移
- [ ] 創建 `.env.local` 和 `.env.cloud`
- [ ] 驗證 Vertex AI LLM 模塊
- [ ] 驗證 LLM Factory 配置
- [ ] 更新 main.py
- [ ] 本地測試 Vertex AI 連接

### 第三階段：容器化
- [ ] 創建 Dockerfile.cloud
- [ ] 構建容器鏡像
- [ ] 推送到 Artifact Registry
- [ ] 本地測試容器

### 第四階段：後端部署
- [ ] 部署到 Cloud Run
- [ ] 配置環境變量和密鑰
- [ ] 配置自動擴展
- [ ] 測試後端 API
- [ ] 配置 IAM 權限

### 第五階段：前端部署
- [ ] 構建前端應用
- [ ] 上傳前端到 Cloud Storage
- [ ] 配置靜態網站託管
- [ ] 配置 CORS 策略
- [ ] 測試前端訪問

### 第六階段：域名配置
- [ ] 創建 Cloud DNS 區域
- [ ] 配置 DNS 記錄
- [ ] 申請 SSL 證書
- [ ] 驗證 HTTPS 連接

### 第七階段：監控設置
- [ ] 設置 Cloud Logging
- [ ] 設置 Cloud Monitoring
- [ ] 配置告警規則
- [ ] 設置通知渠道

### 第八階段：測試上線
- [ ] 功能測試
- [ ] 負載測試（30 人並發）
- [ ] 性能基準測試
- [ ] 安全審計
- [ ] 灰度發布
- [ ] 正式上線

---

## 🚨 常見問題和解決方案

### 問題 1：Vertex AI 連接失敗
```bash
# 解決方案：
# 1. 驗證認證
export GOOGLE_APPLICATION_CREDENTIALS=~/anti-fraudx-key.json
gcloud auth application-default print-access-token

# 2. 驗證 API 已啟用
gcloud services list --enabled | grep aiplatform

# 3. 驗證服務帳戶權限
gcloud projects get-iam-policy gen-lang-client-0029677384
```

### 問題 2：Cloud Run 部署失敗
```bash
# 解決方案：
# 1. 檢查構建日誌
gcloud builds log <BUILD_ID>

# 2. 檢查部署日誌
gcloud run services describe anti-fraudx-backend --region us-central1

# 3. 檢查容器日誌
gcloud logging read "resource.type=cloud_run_revision" --limit 50
```

### 問題 3：DNS 解析失敗
```bash
# 解決方案：
# 1. 驗證 DNS 記錄
gcloud dns record-sets list --zone=anti-fraudx-us-ci

# 2. 檢查 DNS 傳播
nslookup anti-fraudx.us.ci

# 3. 等待 DNS 傳播（通常 5-30 分鐘）
```

---

**文檔版本**: v1.0
**最後更新**: 2026-03-15
**狀態**: 準備就緒

