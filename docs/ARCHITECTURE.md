# AI Anti-Fraud Platform — System Architecture

> Version: 4.1 | Last Updated: 2026-03-11

---

## Overview

Full-stack anti-fraud education platform. Multi-Agent AI system (Scammer + Expert + Victim + Recorder) backed by Ollama (local) or Google Gemini API (cloud). Primary interface: 2D RPG game (`rpg-platform-v2`).

### Core Design Goals

| Goal | Implementation |
|------|----------------|
| Realistic fraud simulation | 4 AI agents, 281 real HK scam cases |
| Local-first privacy | Ollama (Gemma3) on-device |
| Cloud AI option | Gemini API (`gemini-3.1-flash-lite-preview`, runtime-switchable) |
| Low latency | Async parallel generation + streaming + context truncation |
| Knowledge base | ChromaDB RAG — real ADCC/HK scam cases |
| Tooling | Tools Center (`/tools`) — scrape, fine-tune, generate Modelfiles |

---

## High-Level Architecture

```
CLIENT
  rpg-platform-v2 (Phaser.js + TypeScript, port 3000)
  frontend/ (plain HTML/JS, served by FastAPI)
       │ HTTP REST
FASTAPI BACKEND (port 8000)
  API Layer:    rpgv2_game_modes_routes · simulation_routes · tools_routes
                model_switch_routes · training_routes · chat_routes · ...
  Service Layer: AgentService · SimulationRunner · RAGService
  Agent Layer:   ScammerAgent · ExpertAgent · VictimAgent · RecorderAgent
  LLM Layer:     OllamaLlm (local) | GeminiLlm (cloud) — via LlmFactory
  Data Layer:    SQLite · ChromaDB · JSON files · Modelfile.expert/scammer
```

---

## Directory Structure

```
AI-Agentv4/
├── backend/
│   ├── agents/
│   │   ├── prompts/               prompt_builder.py + examples
│   │   ├── scammer.py             ScammerAgent
│   │   ├── expert.py              ExpertAgent
│   │   ├── victim.py              VictimAgent
│   │   ├── recorder.py            RecorderAgent
│   │   ├── base_agent.py          BaseAntifraudAgent
│   │   ├── system_instructions.py Per-agent prompts (281 HK cases embedded)
│   │   └── scam_knowledge_base.json
│   ├── api/
│   │   ├── rpgv2_game_modes_routes.py  PRIMARY game API + trust logic
│   │   ├── tools_routes.py             Tools Center (scraper/finetune/modelgen)
│   │   ├── model_switch_routes.py      LLM provider switch + /api/model/config
│   │   ├── simulation_routes.py        WebSocket simulation
│   │   ├── training_routes.py
│   │   ├── personal_chat_routes.py
│   │   ├── chat_routes.py
│   │   ├── frontend_routes.py          Static file serving
│   │   └── [6 other route files]
│   ├── llms/
│   │   ├── ollama_llm.py          Ollama adapter (shared httpx client, pooling)
│   │   ├── gemini_llm.py          Gemini adapter (streaming, retry backoff)
│   │   ├── llm_factory.py         Provider selection + RAG injection
│   │   ├── llm_utils.py           extract_text_from_contents (shared)
│   │   └── rag_integration.py     GeminiRAGHelper singleton
│   ├── models/
│   │   ├── Modelfile.expert       Anti-fraud expert Ollama model
│   │   └── Modelfile.scammer      Scammer simulation Ollama model
│   ├── scripts/                   25 utility scripts
│   │   ├── scraper.py             ADCC website scraper (Selenium)
│   │   ├── generate_finetuning_data.py  Fine-tune JSONL generator
│   │   ├── model_fine_tuning.py   Generates both Modelfiles in one run
│   │   └── [22 other scripts]
│   ├── services/
│   │   ├── agent_service.py       Agent orchestration + tracking
│   │   └── simulation_runner.py   Full simulation loop
│   ├── utils/                     29 utility modules
│   │   ├── rpgv2_game_mode_manager.py  Session management + Recorder analysis
│   │   ├── performance_tracker.py     VictimTrustState + trust updates
│   │   ├── adaptive_scoring.py        AdaptiveWeightOptimizer (persona-based)
│   │   ├── role_enforcer.py           Role consistency
│   │   ├── scammer_strategy_manager.py
│   │   └── [24 other utils]
│   ├── config.py                  Centralized config (9 dataclass sections)
│   ├── main.py                    FastAPI entry point (15 routers registered)
│   └── requirements.txt
├── rpg-platform-v2/               TypeScript + Phaser.js (port 3000)
│   └── src/scenes/
│       ├── BattleScene.ts         HTML overlay battle UI (PRIMARY)
│       ├── WorldMapScene.ts       2D map + NPC collision
│       ├── AutoModeScene.ts       Automated simulation
│       └── ResultScene.ts         RecorderAgent report display
├── frontend/                      Plain HTML/JS dashboard (9 pages)
│   ├── index.html                 Main dashboard
│   ├── tools.html                 Tools Center (scraper/finetune/modelgen)
│   ├── rpgv2_game_modes.html      Game mode selector
│   └── personal_chat.html
├── RPG_platform/                  Legacy RPG Maker MZ project
├── data/                          Scraped ADCC data
├── docs/                          Documentation
├── quick_start.bat                Primary startup (auto-detects Gemini/Ollama)
└── docker-compose.yml
```

---

## Backend Module Map

### `main.py` — Entry Point

```
main.py
 ├── load_dotenv('backend/.env', override=True)  ← authoritative .env
 ├── offline_mode checks (skipped if Gemini enabled)
 ├── GPU check (FORCE_GPU=0 by default)
 ├── PromptVersionManager initialization
 ├── 15 API routers registered
 │    ├── tools_router         /api/tools/*
 │    ├── model_switch_router  /api/model/*
 │    ├── rpgv2_game_modes_router  /api/rpgv2/*
 │    └── [12 other routers]
 ├── Static mounts: /RPG_Project, /rpgv2-static
 └── Uvicorn on 127.0.0.1:8000
```

### `config.py` — Configuration

| Section | Class | Key Values |
|---------|-------|------------|
| Trust system | `TrustConfig` | Win thresholds, trust change limits, emotional multipliers |
| Simulation | `SimulationConfig` | Max 15 rounds, timing delays |
| LLM (Ollama) | `LLMConfig` | Model names, URLs, num_ctx=4096 |
| Gemini API | `GeminiConfig` | API key, model IDs, GEMINI_ENABLED flag |
| Validation | `ValidationConfig` | Message length, session limits |
| Database | `DatabaseConfig` | SQLite path, ChromaDB path |
| Personas | `PersonaConfig` | elderly/average/overconfident/student |
| Scam tactics | `ScamTacticsConfig` | 10 tactic types |
| Logging | `LoggingConfig` | Log level, file paths |

### `backend/.env` — Single Source of Truth

All runtime config lives in `backend/.env`. The root `.env` is unused.
`main.py` loads it with `load_dotenv('backend/.env', override=True)` before anything else.

> **Important**: Values must NOT have surrounding single quotes (e.g. `GEMINI_ENABLED=true` not `GEMINI_ENABLED='true'`), or Python's `os.getenv` will include the quotes in the string.

---

## Frontend / Game Clients

### rpg-platform-v2 (Primary Interface)

| Scene | Purpose |
|-------|---------|
| `BattleScene.ts` | HTML overlay UI, chat bubbles, trust meter, voice input, session persistence |
| `WorldMapScene.ts` | 2D exploration, NPC collision detection, triggers battle |
| `AutoModeScene.ts` | Fully automated AI-vs-AI simulation |
| `ResultScene.ts` | Displays RecorderAgent's post-game analysis report |

### frontend/ (Web Dashboard — 9 pages)

| Page | Purpose |
|------|---------|
| `index.html` | Main control dashboard |
| `tools.html` | Tools Center: scraper, fine-tune data gen, Modelfile creation, ollama create |
| `rpgv2_game_modes.html` | Game mode selector |
| `personal_chat.html` | Direct 1-on-1 chat with AI agent |
| `dashboard.html` | Training statistics |
| `evaluate.html` | Model evaluation |

---

## Data Flow

### RPGv2 Battle (Primary)

```
Player interacts in BattleScene
  POST /api/rpgv2/game/action
    → rpgv2_game_modes_routes.py
    → AgentService initialized per request (Gemini or Ollama via GEMINI_ENABLED)
    → asyncio.gather(scammer_task, expert_task)  ← parallel generation
    → LlmFactory.create_llm(agent_type)
         GEMINI_ENABLED=true  → GeminiLlm → Google Gemini API (streaming)
         GEMINI_ENABLED=false → OllamaLlm → localhost:11434
    → RAG context injected into system_instruction (ChromaDB query)
    → Trust changes calculated (keyword fast-path → AI semantic judgment)
    → Session updated in RPGv2GameModeManager
    → JSON response to frontend
```

### Tools Center Flow

```
tools.html → /api/tools/scraper/run
  → tools_routes.py → ProcState.start(scraper.py)
  → background thread drains stdout to log_lines
  → /api/tools/scraper/status polls running/exit_code/log

tools.html → /api/tools/modelgen/run
  → model_fine_tuning.py main()
  → creates backend/models/Modelfile.expert
  → creates backend/models/Modelfile.scammer

tools.html → /api/tools/modelgen/ollama-create-both
  → ollama create anti-fraud-expert -f Modelfile.expert  (sequential)
  → ollama create scammer-sim -f Modelfile.scammer
  → log streamed to frontend via /api/tools/modelgen/status
```

### RAG Knowledge Injection

```
LlmFactory.create_llm('scammer', scam_type='investment')
  → GeminiRAGHelper singleton
  → rag_integration.py → ChromaDB query (backend/db/chroma_db/)
  → top-N relevant HK scam cases returned
  → appended to system_instruction before LLM call
```

---

## Key File Dependencies

```
main.py
  └── api/rpgv2_game_modes_routes.py
        └── services/agent_service.py
              └── llms/llm_factory.py
                    ├── llms/ollama_llm.py
                    │     └── llms/llm_utils.py  (shared extract_text_from_contents)
                    ├── llms/gemini_llm.py
                    │     └── google.genai (streaming)
                    └── llms/rag_integration.py
                          └── services/rag_service.py → chromadb
        └── utils/rpgv2_game_mode_manager.py  (GameSession dataclass)
        └── utils/performance_tracker.py      (VictimTrustState)
        └── config.py  (global singleton)
  └── api/tools_routes.py
        └── scripts/scraper.py
        └── scripts/generate_finetuning_data.py
        └── scripts/model_fine_tuning.py  → backend/models/Modelfile.*

rpg-platform-v2/src/main.ts
  └── scenes/WorldMapScene.ts
        └── scenes/BattleScene.ts
              └── services/BackendClient.ts → FastAPI :8000
              └── systems/TrustSystem.ts
              └── ui/TrustMeter.ts
```

---

## Environment Configuration

All configuration lives in `backend/.env`. Key variables:

```bash
# LLM Provider
GEMINI_ENABLED=false          # true = Gemini API, false = Ollama
GEMINI_API_KEY=your_key_here
AGENT_MODEL=gemma3:4b
OLLAMA_BASE_URL=http://localhost:11434

# Performance tuning
OLLAMA_NUM_CTX=2048
OLLAMA_NUM_PREDICT=400
OLLAMA_TEMPERATURE=0.7
GEMINI_MAX_OUTPUT_TOKENS=800

# Per-agent model overrides
GEMINI_MODEL_SCAMMER=gemini-3.1-flash-lite-preview
GEMINI_MODEL_EXPERT=gemini-3.1-flash-lite-preview

# Fine-tuned Ollama model overrides (after running Tools Center)
AGENT_MODEL_SCAMMER=scammer-sim
AGENT_MODEL_EXPERT=anti-fraud-expert

# Database
# SQLite: auto-created at anti_fraud_game.db
# ChromaDB: auto-created at backend/db/chroma_db/

# GPU
FORCE_GPU=0                   # 1 = exit if no GPU found
```

### Known Configuration Pitfalls

| Issue | Cause | Fix |
|-------|-------|-----|
| `GEMINI_ENABLED` always reads as `'false'` | Value wrapped in single quotes in `.env` | Use `GEMINI_ENABLED=true` (no quotes) |
| LLMConfig legacy values | `num_ctx=4096` in config.py conflicts with optimized `ollama_llm.py` values | Sync or remove from config.py |
| Tools not found | `backend/scripts/` not in PATH | `tools_routes.py` uses absolute paths via `SCRIPTS_DIR` |
