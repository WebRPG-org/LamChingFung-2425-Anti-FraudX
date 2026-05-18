# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

This is a multi-agent anti-fraud training platform for Hong Kong. The backend is the composition root: `backend/main.py` loads environment variables, runs startup checks, registers prompt versions, mounts static assets, and wires the API routers together.

The codebase has three main user-facing surfaces:
- `frontend/` — static HTML/CSS/JS pages for mode selection, evaluation, monitoring, and personal chat.
- `RPG_platform/RPG_Project/` — the legacy RPG Maker MV experience.
- `rpg-platform-v2/` — the newer Phaser + TypeScript + Vite RPG client.

The main backend layers are:
- `backend/agents/` — the four core agents: scammer, victim, expert, recorder.
- `backend/api/` — FastAPI route modules grouped by feature area.
- `backend/services/` — orchestration and shared business logic.
- `backend/utils/` — trust scoring, role enforcement, validation, performance tracking, and conversation analysis.
- `backend/llms/` — Ollama, Gemini, and RAG integration helpers.
- `backend/tests/` — pytest suite, including live endpoint and integration-style tests.

Deployment and supporting areas:
- `ansible/` — deployment automation.
- `backend/models/` — Ollama model files and model usage notes.
- `backend/scripts/` — data generation, training, evaluation, and model management utilities.
- `docker-compose.yml` — local stack for backend + Ollama.

## Common commands

Run commands from the repository root unless noted otherwise.

### Backend
```bash
cd backend && pip install -r requirements.txt
cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000
cd backend && python main.py
cd backend && pytest tests -v
cd backend && pytest tests/test_main_endpoints.py -v
cd backend && pytest tests/test_main_endpoints.py::test_health_endpoint -v
cd backend && python tests/test_main_endpoints.py
```

### Frontend RPGv2
```bash
cd rpg-platform-v2 && npm install
cd rpg-platform-v2 && npm run dev
cd rpg-platform-v2 && npm run type-check
cd rpg-platform-v2 && npm run build
cd rpg-platform-v2 && npm run preview
```

### Docker / deployment
```bash
docker-compose up -d
docker-compose logs -f
docker-compose down
cd ansible && pip install -r requirements.txt
cd ansible && ansible-playbook -i inventory/hosts.yml playbooks/site.yml
```

## Architecture notes

- `backend/main.py` mounts `/RPG_Project` and `/rpgv2-static` from local folders, so the root app serves both legacy and v2 game assets.
- The root `/` route prefers `frontend/index.html`; if that file is unavailable, it falls back to the RPG Maker entry page.
- The API layer is split by domain rather than by transport. The important route groups are simulation, training, personal chat, RPG/game flows, prompt versioning, demo mode, monitoring, and model switching.
- The core simulation flow runs through the agent layer and service layer: route handlers call services, services coordinate agents, and utilities handle trust/evaluation/consistency logic.
- Prompt versioning is a first-class concern; startup registers initial prompts and the repo includes routes and scripts for version management and A/B-style comparison.
- The backend startup path enforces offline/data-isolation checks and GPU detection. If `FORCE_GPU=1`, startup exits when GPU validation fails.
- The default backend model is `gemma4:e4b` unless overridden by environment variables.
- `docker-compose.yml` runs two services: Ollama and the backend. The backend container mounts source directories, so local edits are reflected in the container.

## How to think about the code

- There are effectively two active game clients: the older RPG Maker integration and the newer Phaser/Vite client. Do not assume one has replaced the other.
- The newer RPGv2 code is TypeScript-first and should be validated with `npm run type-check` and `npm run build` when changing game logic.
- Backend tests are a mix of unit and integration tests. Some expect a running server at `http://localhost:8000`, and some depend on model/config availability.
- The quickest backend smoke check is `backend/tests/test_main_endpoints.py`, which covers health, root, docs, and game-related endpoints.
- The project is organized around fraud-simulation workflows: auto simulation, interactive chat, RPG-style training, and prompt/evaluation tooling.
