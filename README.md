# Anti-FraudX RPG v2

精簡版專案，只保留現行 `RPG v2` 前端與其所需的 `Vertex AI` 後端。

## 保留範圍

- `rpg-platform-v2/`：RPG v2 前端遊戲
- `backend/main.py`：最小後端入口
- `backend/api/rpgv2_game_modes_routes.py`
- `backend/api/rpgv2_battle_routes.py`
- `backend/api/game_routes_v2.py`
- `backend/api/tts_routes.py`
- `backend/llms/vertex_ai_llm.py`
- `backend/llms/llm_factory.py`
- RPG v2 必需的 agents / services / utils

## 已移除範圍

- 自動模擬模式
- 個人對話模式
- 工具中心
- API 測試模式
- 舊 RPG Maker v1
- 舊 RPG Maker plugins
- 大部分歷史報告與 phase 文件

## 本地啟動

### Backend

```bash
cd backend
python main.py
```

預設端口：`8080`

### RPG v2 前端開發

```bash
cd rpg-platform-v2
npm install
npm run dev
```

## 核心端點

- `/`：最小首頁入口
- `/health`：健康檢查
- `/rpgv2`：RPG v2 HTML 入口
- `/api/rpgv2/game/start`
- `/api/rpgv2/game/action`
- `/api/rpgv2/game/state/{session_id}`
- `/api/tts/synthesize`

## 文件

- `docs/ARCHITECTURE.md`
- `docs/DEPLOYMENT.md`
- `docs/CLEANUP_LOG.md`

## 備註

此版本目標非常明確：
只保留 RPG v2 遊戲主線，其他網站功能不再維護。
