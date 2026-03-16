# Feature Documentation Index

> Version: 4.1 | Last Updated: 2026-03-11

Each feature has its own dedicated document in `docs/features/`. This index provides a quick reference with a one-line summary and links.

---

## Core Features

| Document | Feature | Summary |
|----------|---------|--------|
| [multi-agent-system.md](multi-agent-system.md) | Multi-Agent AI Dialogue | 4 AI agents (Scammer, Expert, Victim, Recorder) running simultaneously with real HK scam case prompts |
| [llm-backend.md](llm-backend.md) | Dual LLM Backend | Provider-agnostic layer switching between local Ollama and cloud Gemini API at runtime |
| [battle-scene.md](battle-scene.md) | RPGv2 Battle Scene | HTML overlay battle UI on the live 2D world map — chat bubbles, voice input, trust meter |
| [trust-meter.md](trust-meter.md) | Trust Meter System | Real-time 3-dimension trust tracking (scammer/expert/alertness) with inertia, fatigue, and emotional modifiers |
| [parallel-generation.md](parallel-generation.md) | Parallel Response Generation | `asyncio.gather()` generates all agent responses simultaneously — ~50% latency reduction |

---

## Secondary Features

| Document | Feature | Summary |
|----------|---------|--------|
| [rag-knowledge-base.md](rag-knowledge-base.md) | RAG Knowledge Base | ChromaDB vector store of 281 real ADCC/HK scam cases injected into agent prompts per request |
| [prompt-versioning.md](prompt-versioning.md) | Prompt Version Management | A/B test different agent prompt versions at runtime without server restart |
| [voice-input.md](voice-input.md) | Voice Input | Browser Web Speech API — Cantonese `zh-HK` recognition with 2s silence auto-stop |
| [session-persistence.md](session-persistence.md) | Session State Persistence | `sessionStorage` save/restore — players continue mid-battle after page refresh |
| [model-switch-api.md](model-switch-api.md) | Model Switch API | REST API to switch between Ollama and Gemini at runtime — no restart needed |
| [personal-chat.md](personal-chat.md) | Personal Chat Mode | Standalone 1-on-1 chat with a single AI agent outside the RPG game |
| [auto-mode.md](auto-mode.md) | Auto Mode (Simulation) | Fully automated AI-vs-AI simulation over WebSocket — used for training data and demos |
| [gpu-detection.md](gpu-detection.md) | GPU Detection | NVIDIA GPU detection via `nvidia-smi` at startup; `FORCE_GPU=1` exits if no GPU found |
| [offline-mode.md](offline-mode.md) | Offline Mode Checks | Startup verification that no data leaves the local network (Ollama mode only) |
| [recorder-agent.md](recorder-agent.md) | RecorderAgent Analysis | Post-session educational report: tactics detected, key moments, recommendations |
| [tools-center.md](tools-center.md) | Tools Center | Web dashboard for full model training pipeline: scrape → finetune → Modelfile → ollama create |
| [adaptive-scoring.md](adaptive-scoring.md) | Adaptive Scoring System | Persona-based evaluation weight adjustment — elderly weights empathy higher, overconfident weights evidence |
| [scammer-strategy.md](scammer-strategy.md) | Scammer Strategy Management | Per-session tactic tracking with fatigue multipliers (50% effectiveness after 4+ uses of same tactic) |

---

## Feature Dependency Map

```
Battle Scene
  ├── Multi-Agent System
  │     ├── LLM Backend (Ollama / Gemini)
  │     │     ├── RAG Knowledge Base
  │     │     └── Prompt Versioning
  │     ├── Recorder Agent
  │     └── Auto Mode (VictimAgent)
  ├── Trust Meter
  │     ├── Adaptive Scoring
  │     └── Scammer Strategy Management
  ├── Parallel Generation
  ├── Voice Input
  └── Session Persistence

Model Switch API
  └── LLM Backend

Tools Center
  ├── RAG Knowledge Base (scraper feeds ChromaDB)
  └── LLM Backend (custom models via per-agent overrides)

GPU Detection        → startup only, no runtime dependency
Offline Mode Checks  → startup only, no runtime dependency
Personal Chat        → LLM Backend (simplified path)
```

---

## Quick File Lookup

| You want to change... | Edit this file |
|-----------------------|---------------|
| Agent personalities / prompts | `backend/agents/system_instructions.py` |
| Win/loss thresholds | `backend/config.py` → `TrustConfig` |
| LLM token limits | `backend/llms/ollama_llm.py` or `gemini_llm.py` |
| RAG result count | `backend/config.py` → `DatabaseConfig.RAG_DEFAULT_RESULTS` |
| Trust fatigue rates | `backend/utils/scammer_strategy_manager.py` |
| Persona starting values | `backend/config.py` → `PersonaConfig` |
| Battle UI layout | `rpg-platform-v2/src/scenes/BattleScene.ts` |
| Voice recognition language | `BattleScene.ts` → `recognition.lang` |
| Training pipeline | `backend/scripts/` + `backend/api/tools_routes.py` |
| API endpoints | `backend/api/rpgv2_game_modes_routes.py` |
