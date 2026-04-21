# Cleanup Log

## Final target

保留 `RPG v2 + Vertex AI minimal backend`，刪除其餘網站功能、舊 RPG、舊部署、舊報告與測試資產。

## Final kept scope

### Frontend
- `frontend/index.html`
- `frontend/js/app.js`
- `frontend/css/style.css`
- `rpg-platform-v2/`

### Backend
- `backend/main.py`
- `backend/api/rpgv2_game_modes_routes.py`
- `backend/api/rpgv2_battle_routes.py`
- `backend/api/game_routes_v2.py`
- `backend/api/tts_routes.py`
- `backend/llms/vertex_ai_llm.py`
- `backend/llms/llm_factory.py`
- RPG v2 所需 agents / services / utils / config

### Docs
- `README.md`
- `docs/ARCHITECTURE.md`
- `docs/DEPLOYMENT.md`
- `docs/CLEANUP_LOG.md`

## Rewritten files
- `frontend/index.html`
- `frontend/js/app.js`
- `backend/main.py`
- `README.md`
- `docs/ARCHITECTURE.md`
- `docs/DEPLOYMENT.md`
- `docs/CLEANUP_LOG.md`

## Deleted categories

### Removed frontend web features
- 自動模擬頁
- 個人對話頁
- 工具中心頁
- API 測試頁
- dashboard / evaluate 類頁面
- 舊模型切換前端腳本

### Removed backend web features
- simulation routes
- personal chat routes
- tools routes
- frontend routes
- training routes
- model switch routes
- chat routes
- rag / evaluation / demo / batch / websocket 類舊 routes
- `backend/main_minimal.py`

### Removed legacy RPG assets
- `RPG_platform/`
- `rpg_maker_plugins/`

### Removed deployment and automation leftovers
- `ansible/`
- `deploy/`
- `docker/`
- multiple `docker-compose*`
- `Dockerfile`
- `Dockerfile.cloud`
- `Dockerfile.frontend`
- old setup / start / validation batch and powershell scripts

### Removed docs and reports
- root-level `PHASE_*`
- root-level `FINAL_*`
- root-level `IMPLEMENTATION_*`
- root-level `DEPLOYMENT_*`
- old guides / checklists / summaries
- `backend/docs/`
- `docs/features/`
- `record_md/`
- backend-level historical RAG reports

### Removed tests and old scripts
- `backend/tests/`
- `scripts/`
- `backend/scripts/`
- multiple legacy test runners and experiment scripts

## Validation summary

### Completed
- homepage simplified to RPG v2 only
- backend routers trimmed to RPG v2 minimum set
- local `/health` endpoint responded successfully
- final kept backend API set verified
- rewritten docs have no linter errors

### Verified health response

```json
{"status":"Backend is running","model_in_use":"gemma3:4b"}
```

## Notes

- 本次清理以「最小保留」為原則。
- `model_in_use` 現時仍顯示 `gemma3:4b`，代表環境變數展示值未完全同步為 Vertex 名稱；但主線結構已收窄為 RPG v2 + Vertex AI backend。
- 如要再進一步，下一步可以專門清理 `requirements.txt` 與剩餘根目錄非必要設定檔。
