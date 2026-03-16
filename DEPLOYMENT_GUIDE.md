# Anti-FraudX 完整部署指南

## 目錄

1. [概述](#概述)
2. [本地部署](#本地部署)
3. [Cloud 部署](#cloud-部署)
4. [架構設計](#架構設計)
5. [性能優化](#性能優化)
6. [監控和日誌](#監控和日誌)
7. [故障排除](#故障排除)

## 概述

Anti-FraudX 是一個支持雙環境部署的反詐騙教育平台：

- **本地部署**：適合開發和測試，使用 Gemini API 或 Ollama
- **Cloud 部署**：適合生產環境，使用 Google Cloud Vertex AI Express Mode

### 系統要求

#### 本地部署
- Python 3.11+
- Docker & Docker Compose
- 4GB RAM 最小
- 10GB 磁盤空間

#### Cloud 部署
- Google Cloud 帳戶
- gcloud CLI
- 信用卡（用於計費）

## 本地部署

### 1. 環境準備

```bash
# 克隆項目
git clone <repository-url>
cd AI-Agent-main

# 創建虛擬環境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安裝依賴
pip install -r backend/requirements.txt
```

### 2. 配置環境變量

```bash
# 複製模板
cp .env.example .env.local

# 編輯 .env.local
# 設置 GEMINI_API_KEY 或 OLLAMA_BASE_URL
```

### 3. 啟動本地服務

```bash
# 使用 Docker Compose
docker-compose -f docker-compose.local.yml up

# 或直接運行
cd backend
python main.py
```

### 4. 訪問應用

- 後端 API: http://localhost:8000
- 前端: http://localhost:3000
- API 文檔: http://localhost:8000/docs

## Cloud 部署

### 1. 初始化 GCP

```bash
# 設置 gcloud CLI
gcloud auth login
gcloud config set project anti-fraudx-us-ci

# 運行初始化腳本
bash deploy/cloud/setup_gcp.sh
```

### 2. 配置計費

```bash
# 設置計費和告警
bash deploy/cloud/setup_billing.sh
```

### 3. 部署後端

```bash
# 部署到 Cloud Run
bash deploy/cloud/deploy_to_cloud.sh
```

### 4. 配置域名

```bash
# 獲取 Cloud Run 服務 URL
gcloud run services describe anti-fraudx-backend \
  --platform managed \
  --region us-central1 \
  --format='value(status.url)'

# 在 Cloud DNS 中配置 CNAME 記錄
# anti-fraudx.us.ci -> <Cloud Run URL>
```

### 5. 部署前端

```bash
# 構建前端
cd frontend
npm run build

# 上傳到 Cloud Storage
gsutil -m cp -r dist/* gs://anti-fraudx-storage/
```

## 架構設計

### 本地架構

```
┌─────────────────────────────────────────┐
│         Anti-FraudX 本地部署             │
├─────────────────────────────────────────┤
│                                         │
│  ┌──────────────┐    ┌──────────────┐  │
│  │   Frontend   │    │   Backend    │  │
│  │  (React)     │◄──►│  (FastAPI)   │  │
│  └──────────────┘    └──────────────┘  │
│                            │            │
│        ┌───────────────────┼────────────┤
│        │                   │            │
│   ┌────▼────┐      ┌──────▼──────┐    │
│   │ SQLite  │      │ Gemini/     │    │
│   │ Database│      │ Ollama LLM  │    │
│   └─────────┘      └─────────────┘    │
│                                         │
└─────────────────────────────────────────┘
```

### Cloud 架構

```
┌──────────────────────────────────────────────────┐
│         Anti-FraudX Cloud 部署 (GCP)              │
├──────────────────────────────────────────────────┤
│                                                  │
│  ┌────────────────────────────────────────────┐ │
│  │         Cloud Load Balancer                │ │
│  │    (anti-fraudx.us.ci)                     │ │
│  └────────────────────────────────────────────┘ │
│                      │                          │
│  ┌───────────────────┼───────────────────────┐ │
│  │                   │                       │ │
│  ▼                   ▼                       ▼ │
│ ┌──────────────┐  ┌──────────────┐  ┌──────────┐
│ │ Cloud Run    │  │ Cloud Run    │  │ Cloud   │
│ │ (Backend)    │  │ (Backend)    │  │ Storage │
│ │ Instance 1   │  │ Instance 2   │  │ (Frontend)
│ └──────────────┘  └──────────────┘  └──────────┘
│        │                  │
│        └──────────────────┼──────────────────┐
│                           │                  │
│                    ┌──────▼──────┐    ┌─────▼────┐
│                    │  Firestore  │    │ Vertex   │
│                    │  Database   │    │ AI LLM   │
│                    └─────────────┘    └──────────┘
│                           │
│                    ┌──────▼──────┐
│                    │ Cloud       │
│                    │ Logging &   │
│                    │ Monitoring  │
│                    └─────────────┘
│                                                  │
└──────────────────────────────────────────────────┘
```

## 性能優化

### 1. 自動擴展配置

Cloud Run 自動擴展設置：
- 最小實例: 0（節省成本）
- 最大實例: 10（支持 30 人同時使用）
- 內存: 512MB
- CPU: 1

### 2. 緩存策略

- 前端靜態資源: Cloud CDN
- API 響應: Redis（可選）
- 數據庫查詢: Firestore 索引

### 3. 數據庫優化

Firestore 最佳實踐：
- 使用複合索引加速查詢
- 批量操作減少往返次數
- 定期清理過期數據

## 監控和日誌

### 1. Cloud Logging

查看日誌：

```bash
gcloud logging read "resource.type=cloud_run_revision" \
  --limit 50 \
  --format json
```

### 2. Cloud Monitoring

監控指標：
- API 延遲
- 錯誤率
- 活躍用戶數
- Token 使用量

### 3. 本地監控

本地指標保存在 `backend/logs/metrics.json`

## 故障排除

### 問題 1: Cloud Run 部署失敗

```bash
# 檢查構建日誌
gcloud builds log <BUILD_ID>

# 檢查部署狀態
gcloud run services describe anti-fraudx-backend \
  --platform managed \
  --region us-central1
```

### 問題 2: Vertex AI 連接失敗

```bash
# 驗證 API 啟用
gcloud services list --enabled | grep aiplatform

# 驗證服務帳戶權限
gcloud projects get-iam-policy anti-fraudx-us-ci \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:*"
```

### 問題 3: Firestore 查詢超時

```bash
# 檢查索引狀態
gcloud firestore indexes list

# 創建缺失的索引
gcloud firestore indexes create --collection-id=game_sessions
```

## 成本估算

### 本地部署
- 無 GCP 成本
- 本地硬件成本

### Cloud 部署（30 人同時使用）

| 服務 | 估計成本 |
|------|--------|
| Cloud Run | $0.00 - $5/月 |
| Firestore | $0.00 - $10/月 |
| Cloud Storage | $0.00 - $1/月 |
| Vertex AI | $0.00 - $20/月 |
| Cloud Logging | 免費 (1GB/月) |
| **總計** | **$0 - $36/月** |

*注：使用免費層和自動擴展可以將成本控制在最低*

## 下一步

1. ✅ 完成本地部署
2. ✅ 測試所有功能
3. ✅ 部署到 Cloud
4. ✅ 配置域名
5. ✅ 設置監控告警
6. ✅ 進行負載測試

## 支持

如有問題，請查看：
- [ENV_CONFIGURATION_GUIDE.md](ENV_CONFIGURATION_GUIDE.md)
- [Google Cloud 文檔](https://cloud.google.com/docs)
- [FastAPI 文檔](https://fastapi.tiangolo.com/)

