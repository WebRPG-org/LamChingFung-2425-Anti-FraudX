# Deployment

## Backend only

```bash
cd backend
python main.py
```

服務預設於 `http://localhost:8080`

### 必要環境變數

建議配置於 `backend/.env`：

```env
VERTEX_AI_MODEL=gemini-2.5-flash-lite
GCP_PROJECT_ID=your-project-id
GCP_LOCATION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
```

如使用 TTS，亦需要對應 Google Cloud 權限。

## RPG v2 frontend

```bash
cd rpg-platform-v2
npm install
npm run dev
```

## Health check

```bash
curl http://localhost:8080/health
```

## Required API

- `POST /api/rpgv2/game/start`
- `POST /api/rpgv2/game/action`
- `GET /api/rpgv2/game/state/{session_id}`
- `POST /api/tts/synthesize`

## Notes

本專案已不再支援：
- 自動模擬網站
- 個人對話網站
- 工具中心網站
- 舊 RPG Maker v1
- 舊混合部署指引
