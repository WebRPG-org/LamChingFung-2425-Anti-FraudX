# AI-Agent 部署指南

## 概述

本項目是一個功能完整的 Web 應用，能夠接收文字、圖片、語音及螢幕錄影求助，並整合「長者模式」。系統包含以下主要功能：

- 多媒體內容分析（文字、圖片、語音、影片）
- 螢幕錄影功能（支援桌面、Android、iOS）
- 長者模式 UI 和語音功能
- CrewAI 深度分析系統
- 模型微調和部署

## 架構組件

### 後端 (FastAPI)
- **位置**: `backend/`
- **功能**: API 服務、多媒體處理、CrewAI 分析
- **端口**: 8000

### 前端 (React + TypeScript)
- **位置**: `frontend/`
- **功能**: 用戶界面、螢幕錄影、長者模式
- **端口**: 5173

### Cloud Functions
- **位置**: `cloud-functions/`
- **功能**: 多媒體處理管道、影片分析
- **觸發器**: Cloud Storage 上傳事件

## 部署步驟

### 1. 本地開發環境

#### 後端設置
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp ../env.example .env
# 編輯 .env 文件，添加你的 API 密鑰
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 前端設置
```bash
cd frontend
npm install
npm run dev
```

#### Docker 部署
```bash
# 構建並啟動所有服務
docker-compose up --build

# 後台運行
docker-compose up -d --build
```

### 2. Google Cloud Platform 部署

#### 準備工作
1. 創建 Google Cloud Project
2. 啟用以下 API：
   - Cloud Run
   - Cloud Storage
   - Cloud Functions
   - Vertex AI
   - Vision API
   - Speech-to-Text API
   - Video Intelligence API

#### 設置環境變量
```bash
export GOOGLE_CLOUD_PROJECT=your-project-id
export GOOGLE_API_KEY=your-google-api-key
export AWS_ACCESS_KEY_ID=your-aws-access-key
export AWS_SECRET_ACCESS_KEY=your-aws-secret-key
```

#### 部署 Cloud Functions
```bash
cd cloud-functions/video-analysis
npm install
gcloud functions deploy analyzeVideo \
  --runtime nodejs18 \
  --trigger-bucket=ai-agent-videos \
  --set-env-vars=GOOGLE_API_KEY=$GOOGLE_API_KEY
```

#### 部署到 Cloud Run
```bash
# 使用 Cloud Build
gcloud builds submit --config deploy/cloud-build.yaml

# 或手動部署
gcloud run deploy ai-agent-backend \
  --image gcr.io/$GOOGLE_CLOUD_PROJECT/ai-agent-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

### 3. 模型微調部署

#### 準備訓練數據
```python
# 創建訓練數據格式
training_data = [
    {
        "input": "用戶輸入的文字",
        "output": {
            "risk_level": "high",
            "safety_suggestions": ["建議1", "建議2"],
            "analysis": "分析結果"
        }
    }
]
```

#### 使用 Vertex AI 微調
```bash
# 上傳訓練數據到 Cloud Storage
gsutil cp training_data.json gs://your-bucket/training/

# 創建微調作業
gcloud ai custom-jobs create \
  --region=us-central1 \
  --display-name="ai-agent-fine-tuning" \
  --config=vertex_ai_config.yaml
```

#### 部署微調模型
```bash
# 部署到 Vertex AI Model Registry
gcloud ai models upload \
  --region=us-central1 \
  --display-name="ai-agent-fine-tuned" \
  --container-image-uri=gcr.io/cloud-aiplatform/prediction/pytorch-gpu.1-9
```

## 功能配置

### 長者模式設置
- 語音播報：使用瀏覽器 SpeechSynthesis API
- 大字體：CSS 類 `.elder-large-text`
- 高對比度：CSS 類 `.elder-high-contrast`
- 簡化界面：CSS 類 `.elder-simplified-ui`

### 螢幕錄影功能
- **桌面/Android**: WebRTC API
- **iOS**: 圖文教學 + 手動上傳
- **格式支援**: WebM, MP4, MOV

### CrewAI 分析流程
1. 詐騙分析專家：識別風險指標
2. 風險評估專家：評估風險等級
3. 安全顧問：提供安全建議
4. 時間軸分析師：創建事件時間軸

## 監控和日誌

### 健康檢查
```bash
curl http://localhost:8000/health
```

### 查看日誌
```bash
# Docker 日誌
docker-compose logs backend
docker-compose logs frontend

# Cloud Run 日誌
gcloud run services logs read ai-agent-backend --region=us-central1

# Cloud Functions 日誌
gcloud functions logs read analyzeVideo
```

## 故障排除

### 常見問題

1. **CORS 錯誤**
   - 檢查 `main.py` 中的 CORS 設置
   - 確保前端 URL 在允許列表中

2. **API 密鑰錯誤**
   - 檢查 `.env` 文件中的 API 密鑰
   - 確保密鑰有正確的權限

3. **螢幕錄影不工作**
   - 檢查瀏覽器權限設置
   - 確保使用 HTTPS（生產環境）

4. **長者模式語音不工作**
   - 檢查瀏覽器是否支援 SpeechSynthesis
   - 確保語言設置為繁體中文

### 性能優化

1. **後端優化**
   - 使用 Redis 緩存
   - 異步處理長時間任務
   - 數據庫連接池

2. **前端優化**
   - 代碼分割
   - 圖片壓縮
   - 懶加載

3. **Cloud Functions 優化**
   - 設置適當的記憶體和超時
   - 使用 Cloud Storage 觸發器
   - 並行處理

## 安全考慮

1. **API 安全**
   - JWT 令牌驗證
   - 速率限制
   - 輸入驗證

2. **數據保護**
   - 加密敏感數據
   - 安全的文件上傳
   - 定期清理臨時文件

3. **隱私保護**
   - 不存儲個人敏感信息
   - 自動刪除分析結果
   - 符合 GDPR 要求

## 擴展功能

### 未來改進
1. 支援更多語言
2. 增加更多多媒體格式
3. 改進長者模式體驗
4. 添加更多分析模型

### 集成選項
1. 第三方防詐騙服務
2. 銀行 API 集成
3. 政府數據源
4. 社交媒體監控

## 支援

如有問題，請聯繫：
- 技術支援：support@ai-agent.com
- 文檔：https://docs.ai-agent.com
- GitHub：https://github.com/your-org/ai-agent

