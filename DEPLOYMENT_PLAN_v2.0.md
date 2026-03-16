# Anti-FraudX 完整部署計劃書 v2.0

## 📋 項目概述

| 項目 | 詳情 |
|------|------|
| **項目名稱** | Anti-FraudX |
| **項目 ID** | gen-lang-client-0029677384 |
| **域名** | anti-fraudx.us.ci |
| **用戶容量** | 30 人同時使用 |
| **部署方式** | Google Cloud Platform |
| **LLM 方案** | Vertex AI Express Mode |
| **月度成本** | $0.20（完全免費） |
| **預期完成時間** | 2-3 週 |

---

## 🎯 核心要求

✅ **完全免費部署**（月度 $0.20，只有 DNS 費用）
✅ **Vertex AI Express Mode**（無需管理端點）
✅ **支持 30 人同時使用**（Cloud Run 自動擴展）
✅ **保留所有本地部署文件**（防止本地部署失效）
✅ **統一命名規範**（所有資源使用 anti-fraudx 前綴）
✅ **完整功能集成**（RPG v2、AI 對話、個人對話、自動模擬）
✅ **自定義域名**（anti-fraudx.us.ci）
✅ **雙環境支持**（本地 + Cloud）

---

## 🏗️ 架構設計

### 系統架構圖

```
┌─────────────────────────────────────────────────────────────┐
│                        用戶 (30人)                           │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
        ┌────────────────────────────────┐
        │   anti-fraudx.us.ci (域名)     │
        │   Cloud DNS ($0.20/月)         │
        └────────────────┬───────────────┘
                         │
                         ▼
        ┌────────────────────────────────┐
        │  Cloud Run (200 萬次調用/月)   │
        │  anti-fraudx-backend           │
        │  自動擴展 (支持 30 人並發)     │
        └────────────────┬───────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
   ┌─────────┐    ┌──────────┐    ┌──────────┐
   │Vertex AI│    │Firestore │    │Cloud     │
   │Express  │    │(50K讀/天)│    │Storage   │
   │Mode     │    │anti-fraudx-db │(5GB)    │
   │(免費)   │    │(免費)    │    │(免費)    │
   └─────────┘    └──────────┘    └──────────┘
        │                │                │
        └────────────────┼────────────────┘
                         │
                         ▼
        ┌────────────────────────────────┐
        │  Cloud Storage (前端靜態文件)  │
        │  anti-fraudx-storage           │
        │  (5GB 免費)                    │
        └────────────────┬───────────────┘
                         │
                         ▼
        ┌────────────────────────────────┐
        │  Cloud Logging & Monitoring    │
        │  anti-fraudx-logs              │
        │  (完全免費)                    │
        └────────────────────────────────┘
```

---

## 📁 文件結構設計

### 保留本地部署（✅ 不修改）

```
AI-Agent-main/
├── backend/
│   ├── llms/
│   │   └── gemini_llm.py              ✅ 保留（本地用）
│   ├── main.py                         ✅ 保留並擴展
│   ├── .env                            ✅ 保留（重命名為 .env.local）
│   └── anti_fraud_game.db              ✅ 保留
├── docker-compose.local.yml            ✅ 保留
├── Dockerfile                          ✅ 保留（重命名為 Dockerfile.local）
├── quick_start.bat                     ✅ 保留
└── setup.bat                           ✅ 保留
```

### 新增 Cloud 部署（🆕 不影響本地）

```
AI-Agent-main/
├── backend/
│   ├── llms/
│   │   ├── vertex_ai_llm.py           🆕 新增（Cloud 用）
│   │   └── llm_factory.py             🆕 新增（自動選擇）
│   ├── .env.local                      🆕 新增（本地配置）
│   ├── .env.cloud                      🆕 新增（Cloud 配置）
│   └── .env.example                    🆕 新增（模板）
├── Dockerfile.cloud                    🆕 新增（Cloud Run）
├── docker-compose.cloud.yml            🆕 新增（Cloud 部署）
├── deploy/
│   ├── local/                          🆕 整理現有腳本
│   │   ├── quick_start.bat
│   │   └── setup.bat
│   └── cloud/                          🆕 新增（Cloud 部署）
│       ├── setup_gcp.sh
│       ├── deploy_to_cloud.sh
│       └── rollback.sh
├── docs/
│   ├── LOCAL_DEPLOYMENT.md             🆕 本地部署文檔
│   ├── CLOUD_DEPLOYMENT.md             🆕 Cloud 部署文檔
│   └── NAMING_CONVENTION.md            🆕 命名規範文檔
└── .gitignore                          🆕 更新（排除敏感文件）
```

---

## 🔄 雙環境支持

### LLM 工廠模式（自動選擇）

```python
# backend/llms/llm_factory.py
def get_llm_instance():
    deployment_env = os.getenv("DEPLOYMENT_ENV", "local")
    
    if deployment_env == "cloud":
        # Cloud 部署：使用 Vertex AI Express Mode
        from llms.vertex_ai_llm import VertexAILLM
        return VertexAILLM(
            model_name=os.getenv("VERTEX_AI_MODEL", "gemini-3.1-flash"),
            project_id=os.getenv("GCP_PROJECT_ID", "gen-lang-client-0029677384")
        )
    else:
        # 本地部署：使用 Gemini API
        from llms.gemini_llm import GeminiLLM
        return GeminiLLM()
```

### 環境配置

#### `.env.local`（本地部署）
```bash
DEPLOYMENT_ENV=local
PROJECT_ID=anti-fraudx-local
GEMINI_ENABLED=true
GEMINI_API_KEY=your_api_key_here
OLLAMA_BASE_URL=http://localhost:11434
DATABASE_TYPE=sqlite
DATABASE_PATH=./anti_fraud_game.db
STORAGE_TYPE=local
STORAGE_PATH=./backend/uploads
```

#### `.env.cloud`（Cloud 部署）
```bash
DEPLOYMENT_ENV=cloud
PROJECT_ID=gen-lang-client-0029677384
GCP_PROJECT_ID=gen-lang-client-0029677384
GCP_LOCATION=us-central1
USE_VERTEX_AI=true
VERTEX_AI_MODEL=gemini-3.1-flash
DATABASE_TYPE=firestore
FIRESTORE_PROJECT_ID=gen-lang-client-0029677384
FIRESTORE_DATABASE=anti-fraudx-db
STORAGE_TYPE=gcs
CLOUD_STORAGE_BUCKET=anti-fraudx-storage
CLOUD_RUN_SERVICE=anti-fraudx-backend
DOMAIN_NAME=anti-fraudx.us.ci
```

---

## 💰 成本分析

### 月度成本（完全免費）

| 服務 | 免費額度 | 月度成本 |
|------|--------|--------|
| Cloud Run | 200 萬次調用 | **$0** |
| Vertex AI Express Mode | $300/月免費額度 | **$0** |
| Firestore | 50,000 讀/天 | **$0** |
| Cloud Storage | 5 GB | **$0** |
| Cloud Logging | 50 GB/月 | **$0** |
| Cloud Monitoring | 無限制 | **$0** |
| Cloud DNS | $0.20/區域 | **$0.20** |
| **總計** | | **$0.20/月** |

### 3 個月後成本

- **繼續使用 Vertex AI**：$50-100/月
- **切換到 Ollama**：$0/月（自託管）
- **混合方案**：$0-50/月

---

## 📊 統一命名規範

### Google Cloud 資源

```bash
PROJECT_ID=gen-lang-client-0029677384
PROJECT_NAME=Anti-FraudX
REGION=us-central1
DOMAIN=anti-fraudx.us.ci

# Cloud Run
BACKEND_SERVICE=anti-fraudx-backend
FRONTEND_SERVICE=anti-fraudx-frontend

# 容器鏡像
BACKEND_IMAGE=us-central1-docker.pkg.dev/gen-lang-client-0029677384/anti-fraudx-repo/anti-fraudx-backend
FRONTEND_IMAGE=us-central1-docker.pkg.dev/gen-lang-client-0029677384/anti-fraudx-repo/anti-fraudx-frontend

# 數據庫
FIRESTORE_DATABASE=anti-fraudx-db

# 存儲
STORAGE_BUCKET=anti-fraudx-storage

# DNS
DNS_ZONE=anti-fraudx-us-ci
DNS_NAME=anti-fraudx.us.ci

# 服務帳戶
SERVICE_ACCOUNT=anti-fraudx-sa@gen-lang-client-0029677384.iam.gserviceaccount.com

# 密鑰
GEMINI_API_KEY_SECRET=anti-fraudx-gemini-api-key
VERTEX_AI_KEY_SECRET=anti-fraudx-vertex-ai-key

# 監控
LOG_SINK=anti-fraudx-logs
MONITORING_DASHBOARD=anti-fraudx-dashboard
ALERT_POLICY=anti-fraudx-alerts
```

---

## 🚀 部署階段

### 第一階段：準備（1-2 天）
- [ ] 使用現有 Google Cloud 項目 gen-lang-client-0029677384
- [ ] 啟用必要 API
- [ ] 設置 IAM 角色和服務帳戶
- [ ] 配置計費告警

### 第二階段：代碼遷移（2-3 天）
- [ ] 創建 `backend/llms/vertex_ai_llm.py`
- [ ] 創建 `backend/llms/llm_factory.py`
- [ ] 更新 `backend/main.py` 支持雙環境
- [ ] 創建 `.env.local` 和 `.env.cloud`
- [ ] 本地測試 Vertex AI 連接

### 第三階段：容器化（1-2 天）
- [ ] 創建 `Dockerfile.cloud`
- [ ] 構建容器鏡像
- [ ] 推送到 Artifact Registry
- [ ] 測試容器運行

### 第四階段：後端部署（2-3 天）
- [ ] 部署到 Cloud Run
- [ ] 配置環境變量
- [ ] 設置自動擴展策略
- [ ] 配置 IAM 權限
- [ ] 測試 API 端點

### 第五階段：前端部署（1-2 天）
- [ ] 構建前端應用
- [ ] 上傳到 Cloud Storage
- [ ] 配置靜態網站託管
- [ ] 配置 CORS 策略

### 第六階段：域名配置（1 天）
- [ ] 創建 Cloud DNS 區域
- [ ] 配置 DNS 記錄
- [ ] 申請 SSL 證書
- [ ] 驗證 HTTPS 連接

### 第七階段：監控設置（1 天）
- [ ] 設置 Cloud Logging
- [ ] 設置 Cloud Monitoring
- [ ] 配置告警規則
- [ ] 創建監控儀表板

### 第八階段：測試上線（2-3 天）
- [ ] 功能測試
- [ ] 負載測試（30 人並發）
- [ ] 性能基準測試
- [ ] 安全審計
- [ ] 灰度發布
- [ ] 正式上線

---

## ✅ 功能集成清單

### RPG v2 遊戲
- [ ] 驗證遊戲在 Cloud Run 上正常運行
- [ ] 驗證 NPC 對話系統
- [ ] 驗證地圖和碰撞檢測
- [ ] 驗證 E 鍵互動

### AI 對話系統
- [ ] 驗證 Vertex AI 推理
- [ ] 驗證騙徒角色生成
- [ ] 驗證防詐專家角色生成
- [ ] 驗證受害者角色生成

### 個人對話模式
- [ ] 驗證一對一對話
- [ ] 驗證角色切換
- [ ] 驗證 10 種騙局類型
- [ ] 驗證對話歷史保存

### 自動模擬模式
- [ ] 驗證三方自動對話
- [ ] 驗證對話流程
- [ ] 驗證結果分析
- [ ] 驗證訓練數據生成

### 數據存儲
- [ ] 驗證 Firestore 用戶數據存儲
- [ ] 驗證會話數據存儲
- [ ] 驗證對話歷史存儲
- [ ] 驗證訓練數據存儲

### 文件存儲
- [ ] 驗證 Cloud Storage 文件上傳
- [ ] 驗證文件下載
- [ ] 驗證文件刪除
- [ ] 驗證存儲配額

---

## 🔐 安全考慮

### 認證 & 授權
- [ ] 配置 Cloud IAM 角色
- [ ] 設置服務帳戶權限
- [ ] 配置 API 密鑰管理
- [ ] 實現 JWT 令牌驗證

### 數據加密
- [ ] 配置 TLS/SSL
- [ ] 啟用 Cloud Storage 加密
- [ ] 啟用 Firestore 加密
- [ ] 配置密鑰管理

### 監控和審計
- [ ] 啟用 Cloud Audit Logs
- [ ] 配置安全告警
- [ ] 實現訪問日誌
- [ ] 定期安全審計

---

## 📈 性能優化

### Cloud Run 配置
- [ ] 設置最小實例數：0
- [ ] 設置最大實例數：10
- [ ] 設置 CPU：1
- [ ] 設置內存：512 MB
- [ ] 設置超時：3600 秒

### 自動擴展策略
- [ ] CPU 利用率 > 80% 時擴展
- [ ] 內存利用率 > 80% 時擴展
- [ ] 並發請求 > 100 時擴展

### 緩存策略
- [ ] 實現 Firestore 查詢緩存
- [ ] 實現 API 響應緩存
- [ ] 實現 CDN 緩存

---

## 📝 部署命令

### 初始化 GCP

```bash
# 設置現有項目
gcloud config set project gen-lang-client-0029677384

# 啟用 API
gcloud services enable \
  run.googleapis.com \
  aiplatform.googleapis.com \
  firestore.googleapis.com \
  storage.googleapis.com \
  logging.googleapis.com \
  monitoring.googleapis.com \
  dns.googleapis.com \
  artifactregistry.googleapis.com

# 創建服務帳戶
gcloud iam service-accounts create anti-fraudx-sa \
  --display-name="Anti-FraudX Service Account"
```

### 部署後端

```bash
# 構建容器
docker build -f Dockerfile.cloud -t us-central1-docker.pkg.dev/gen-lang-client-0029677384/anti-fraudx-repo/anti-fraudx-backend:latest .

# 推送到 Artifact Registry
docker push us-central1-docker.pkg.dev/gen-lang-client-0029677384/anti-fraudx-repo/anti-fraudx-backend:latest

# 部署到 Cloud Run
gcloud run deploy anti-fraudx-backend \
  --image us-central1-docker.pkg.dev/gen-lang-client-0029677384/anti-fraudx-repo/anti-fraudx-backend:latest \
  --platform managed \
  --region us-central1 \
  --memory 512Mi \
  --cpu 1 \
  --env-vars-file .env.cloud \
  --allow-unauthenticated
```

### 配置域名

```bash
# 創建 DNS 區域
gcloud dns managed-zones create anti-fraudx-us-ci \
  --dns-name=anti-fraudx.us.ci

# 配置 DNS 記錄
gcloud dns record-sets create anti-fraudx.us.ci \
  --rrdatas=[CLOUD_RUN_IP] \
  --ttl=300 \
  --type=A \
  --zone=anti-fraudx-us-ci
```

---

## 🎯 成功標準

✅ 系統支持 30 人同時使用
✅ 平均響應時間 < 500ms
✅ 99.9% 可用性
✅ 自動故障轉移
✅ 完整的監控和告警
✅ 月度成本 $0.20
✅ 所有功能完美集成
✅ 本地部署文件完整保留
✅ 統一命名規範應用
✅ 安全審計通過

---

## 📞 支持和維護

### 日常監控
- 實時性能監控
- 自動告警通知
- 日誌分析

### 定期維護
- 每週性能檢查
- 每月安全審計
- 每季度成本優化

### 災難恢復
- 自動備份（每 15 分鐘）
- 故障轉移（< 1 分鐘）
- 恢復時間目標 (RTO)：1 小時
- 恢復點目標 (RPO)：15 分鐘

---

## 📚 相關文檔

- [Vertex AI Express Mode 文檔](https://cloud.google.com/vertex-ai/docs/generative-ai/start/quickstarts/api-quickstart)
- [Cloud Run 部署指南](https://cloud.google.com/run/docs/quickstarts/build-and-deploy)
- [Firestore 文檔](https://cloud.google.com/firestore/docs)
- [Cloud Storage 文檔](https://cloud.google.com/storage/docs)
- [Cloud DNS 文檔](https://cloud.google.com/dns/docs)

---

**文檔版本**: v2.0
**最後更新**: 2026-03-15
**狀態**: 準備就緒
