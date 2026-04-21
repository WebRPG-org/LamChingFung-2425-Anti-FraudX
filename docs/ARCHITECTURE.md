# Architecture

## Scope

此專案已精簡為單一主線：`RPG v2 + Vertex AI backend`。

## Frontend

### `rpg-platform-v2/`
- Phaser + TypeScript 遊戲前端
- 透過 `BackendClient` 呼叫 backend
- 主要使用：
  - `/health`
  - `/api/rpgv2/game/start`
  - `/api/rpgv2/game/action`
  - `/api/rpgv2/game/state/{session_id}`
  - `/api/tts/synthesize`

### `frontend/index.html`
- 只保留一個用途：打開雲端 RPG v2 前端

## Backend

### Entry
- `backend/main.py`
  - 提供首頁
  - 提供 `/health`
  - 掛載 `rpg-platform-v2` 靜態資源
  - 只載入 RPG v2 必需 routers

### Preserved routers
- `backend/api/rpgv2_game_modes_routes.py`
- `backend/api/rpgv2_battle_routes.py`
- `backend/api/game_routes_v2.py`
- `backend/api/tts_routes.py`

### AI stack
- `backend/llms/llm_factory.py`
- `backend/llms/vertex_ai_llm.py`

### Core runtime modules
- `backend/services/agent_service.py`
- `backend/agents/scammer.py`
- `backend/agents/expert.py`
- `backend/agents/victim.py`
- `backend/agents/recorder.py`
- `backend/utils/rpgv2_game_mode_manager.py`
- `backend/utils/scam_scoring_hybrid.py`

## Removed architecture branches

已移除或準備移除：
- 自動模擬網站分支
- 個人對話網站分支
- 工具中心分支
- 測試頁分支
- RPG Maker v1 分支

## Deployment model

- 前端主遊戲可獨立部署為雲端靜態前端
- backend 維持 RPG v2 所需最小 API
- AI 回應主線為 Vertex AI
