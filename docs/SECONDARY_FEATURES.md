# AI Anti-Fraud Platform — Secondary Features

> Version: 4.1 | Last Updated: 2026-03-11

This document describes **supporting features** that enhance the platform's core functionality.

---

## Table of Contents

1. [RAG Knowledge Base](#1-rag-knowledge-base)
2. [Prompt Version Management](#2-prompt-version-management)
3. [Voice Input (Web Speech API)](#3-voice-input-web-speech-api)
4. [Session State Persistence](#4-session-state-persistence)
5. [Model Switch API](#5-model-switch-api)
6. [Personal Chat Mode](#6-personal-chat-mode)
7. [Auto Mode (Simulation)](#7-auto-mode-simulation)
8. [GPU Detection](#8-gpu-detection)
9. [Offline Mode Checks](#9-offline-mode-checks)
10. [RecorderAgent Analysis](#10-recorderagent-analysis)
11. [Tools Center](#11-tools-center)
12. [Adaptive Scoring System](#12-adaptive-scoring-system)
13. [Scammer Strategy Management](#13-scammer-strategy-management)

---

## 1. RAG Knowledge Base

### What It Does

Retrieves **real Hong Kong scam cases** from a vector database and injects them into AI agent prompts, grounding the simulation in actual ADCC-documented fraud patterns.

### How It Works

1. Real HK scam cases are stored in **ChromaDB** (`backend/db/chroma_db/`) as vector embeddings.
2. `LlmFactory.get_rag_context(scam_type)` queries ChromaDB for top-N most relevant cases.
3. Retrieved cases are appended to the agent's system instruction before the LLM call.
4. `GeminiRAGHelper` is a **singleton** — one instance shared across all requests.

### Relevant Files

| File | Purpose |
|------|--------|
| `backend/llms/rag_integration.py` | `GeminiRAGHelper` — formats ChromaDB results for prompt injection |
| `backend/services/rag_service.py` | Low-level ChromaDB `query_db()` |
| `backend/llms/rag_diagnostics.py` | Health check and diagnostics |
| `backend/db/chroma_db/` | Persistent ChromaDB vector store |
| `backend/agents/scam_knowledge_base.json` | Structured scam case data (JSON backup, 281 cases) |
| `data/` | Raw scraped ADCC data (input to embedding pipeline) |

### Configuration (`config.py` → `DatabaseConfig`)

```python
CHROMA_PATH = 'backend/db/chroma_db'
CHROMA_COLLECTION_NAME = 'scam_cases'
RAG_DEFAULT_RESULTS = 3
RAG_MAX_RESULTS = 10
```

---

## 2. Prompt Version Management

### What It Does

Allows **A/B testing of different prompt versions** without restarting the server. Tracks which prompt version produced better outcomes.

### Relevant Files

| File | Purpose |
|------|--------|
| `backend/utils/prompt_version_manager.py` | Core versioning — register, retrieve, compare versions |
| `backend/services/prompt_helper.py` | Registers initial prompt versions at startup |
| `backend/api/prompt_version_routes.py` | REST API to list/switch/compare versions |
| `backend/data/prompt_versions.json` | Persisted version history |

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/prompts/versions` | List all registered versions |
| POST | `/api/prompts/switch` | Switch active version for an agent |
| GET | `/api/prompts/compare` | Compare performance metrics across versions |

### Startup Registration

`main.py` calls `register_initial_prompts(version_manager)` from `services/prompt_helper.py` before the server accepts requests.

---

## 3. Voice Input (Web Speech API)

### What It Does

Allows players to **speak their responses** in the battle scene using the browser's built-in speech recognition.

### Implementation (`rpg-platform-v2/src/scenes/BattleScene.ts`)

```typescript
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
recognition.lang = 'zh-HK';           // Cantonese
recognition.continuous = false;
recognition.interimResults = true;    // Show partial results while speaking
// Auto-stop after 2 seconds of silence
```

### Requirements

- HTTPS or `localhost` environment
- Chrome or Edge browser (best support)
- Microphone permission granted by user

---

## 4. Session State Persistence

### What It Does

Preserves battle state across **page refreshes** so players continue where they left off.

### Implementation (`BattleScene.ts`)

```typescript
// Saved to sessionStorage on every state change:
{
  session_id: string,
  scamType: string,
  messages: ChatMessage[],
  trustData: { scammer: number, expert: number, alertness: number },
  round: number
}
// Restored on BattleScene.create() via tryRestoreState()
// Only restores if scamType matches (prevents cross-NPC contamination)
```

### Key Methods

| Method | Purpose |
|--------|---------|
| `saveState()` | Serializes current state to `sessionStorage` |
| `tryRestoreState()` | Reads `sessionStorage`; restores if `scamType` matches |
| `renderAllBubbles()` | Re-renders all saved messages after restore |

---

## 5. Model Switch API

### What It Does

Allows **runtime switching** between Ollama and Gemini without restarting the backend.

### Relevant Files

| File | Purpose |
|------|--------|
| `backend/api/model_switch_routes.py` | REST API for switching LLM provider |
| `backend/llms/llm_factory.py` | `get_current_provider()`, `get_provider_info()` |

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/model/current` | Get current provider and model info |
| POST | `/api/model/switch` | Switch to `ollama` or `gemini` |
| GET | `/api/model/validate` | Validate current provider configuration |
| GET | `/api/model/config` | Full config dump for current provider |

---

## 6. Personal Chat Mode

### What It Does

Provides a **one-on-one chat interface** (outside the RPG game) where a user can talk directly with a single AI agent for educational purposes.

### Relevant Files

| File | Purpose |
|------|--------|
| `backend/api/personal_chat_routes.py` | REST API for personal chat sessions |
| `frontend/personal_chat.html` | Chat UI |

---

## 7. Auto Mode (Simulation)

### What It Does

Runs a **fully automated simulation** where VictimAgent responds automatically — no human player needed. Used for training data generation and system testing.

### Relevant Files

| File | Purpose |
|------|--------|
| `rpg-platform-v2/src/scenes/AutoModeScene.ts` | Frontend auto-mode scene |
| `backend/api/simulation_routes.py` | WebSocket endpoint for real-time simulation events |
| `backend/services/simulation_runner.py` | Runs the simulation loop |

### Flow

```
AutoModeScene → WebSocket /ws/simulate
  → SimulationRunner.run_simulation()
    → ScammerAgent + ExpertAgent + VictimAgent (parallel)
    → Trust updates after each round
    → Broadcasts events via WebSocket
    → Stops at outcome or max rounds (15)
```

---

## 8. GPU Detection

### What It Does

Checks for available NVIDIA GPU at startup and configures Ollama to use GPU acceleration.

### Relevant Files

| File | Purpose |
|------|--------|
| `backend/utils/gpu_checker.py` | `check_and_enforce_gpu()` — detects NVIDIA GPU via `nvidia-smi` |

### Behaviour

- `FORCE_GPU=0` (default) — logs warning if no GPU found, continues anyway.
- `FORCE_GPU=1` — server exits with error if no GPU detected.
- GPU name and memory logged on detection.
- `gpu_status.json` is **not** cached; regenerated fresh on each startup.

---

## 9. Offline Mode Checks

### What It Does

Verifies that **no data leaves the local network** when running in privacy mode (Ollama only).

### Relevant Files

| File | Purpose |
|------|--------|
| `backend/utils/offline_mode.py` | `check_offline_mode()`, `check_data_isolation()`, `verify_ollama_local_only()` |

### Checks Performed

1. `check_offline_mode()` — Verifies `GEMINI_ENABLED=false`.
2. `check_data_isolation()` — Confirms no external API keys are configured.
3. `verify_ollama_local_only()` — Confirms `OLLAMA_BASE_URL` points to localhost.

> When `GEMINI_ENABLED=true`, these checks are skipped (data intentionally leaves to Google API).

---

## 10. RecorderAgent Analysis

### What It Does

At the end of a battle session, generates a **detailed analysis report** covering scam tactics used, victim decision points, and educational recommendations.

### Relevant Files

| File | Purpose |
|------|--------|
| `backend/agents/recorder.py` | RecorderAgent class |
| `backend/utils/rpgv2_game_mode_manager.py` | `GameSession.round_logs` — per-round data fed to Recorder |
| `rpg-platform-v2/src/scenes/ResultScene.ts` | Displays analysis report in-game |

### Report Contents

- Session outcome (scammer win / expert win / ongoing)
- Scammer tactics identified
- Key decision moments from `round_logs`
- Educational recommendations
- Trust progression data
- Scores: `player_score`, `ai_score`

---

## 11. Tools Center

### What It Does

Provides a **web-based tooling dashboard** (`frontend/tools.html`) for the full model training pipeline — from scraping live scam data to creating custom Ollama models — all runnable without touching the terminal.

### Architecture

```
tools.html  →  /api/tools/*  (tools_routes.py)

Three independent ProcState instances:
  _scraper   — scraper.py
  _finetune  — generate_finetuning_data.py
  _modelgen  — model_fine_tuning.py

Each ProcState:
  .start(cmd)     → subprocess.Popen + background drain thread
  .status()       → { running, exit_code, log[] }
  .running        → bool (polls subprocess.poll())
```

### Pipeline Steps

| Step | UI Button | Backend | Output |
|------|-----------|---------|--------|
| 1. Scrape ADCC data | "執行爬蟲" | `scripts/scraper.py` | `data/scraped_alerts.json` |
| 2. Generate fine-tune data | "生成Fine-Tune數據" | `scripts/generate_finetuning_data.py` | `backend/training_data/fine_tuning_data/*.jsonl` |
| 3. Generate Modelfiles | "生成 Modelfile" | `scripts/model_fine_tuning.py` | `backend/models/Modelfile.expert` + `Modelfile.scammer` |
| 4. Create Ollama models | "建立兩個模型" | `ollama create` via subprocess | Custom Ollama models in `~/.ollama/models/` |

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/tools/scraper/run` | Start scraper process |
| GET | `/api/tools/scraper/status` | Poll scraper status + scraped count |
| POST | `/api/tools/finetune/run` | Start fine-tune data generation |
| GET | `/api/tools/finetune/status` | Poll finetune status + file count |
| GET | `/api/tools/finetune/files` | List generated JSONL files |
| POST | `/api/tools/modelgen/run` | Generate both Modelfiles |
| GET | `/api/tools/modelgen/status` | Poll modelgen status + model files |
| POST | `/api/tools/modelgen/ollama-create-both` | `ollama create` for expert + scammer |
| POST | `/api/tools/modelgen/ollama-create` | `ollama create` for single model |
| GET | `/api/tools/modelgen/ollama-list` | List installed Ollama models |

### Using Custom Models After Creation

After running the full pipeline and creating Ollama models, set in `backend/.env`:

```bash
AGENT_MODEL_SCAMMER=scammer-sim
AGENT_MODEL_EXPERT=anti-fraud-expert
```

`LlmFactory` will use these per-agent overrides on the next request.

---

## 12. Adaptive Scoring System

### What It Does

Dynamically adjusts evaluation weights for expert and scammer responses based on the victim's persona, improving scoring accuracy for different player profiles.

### Implementation (`backend/utils/adaptive_scoring.py`)

`AdaptiveWeightOptimizer` holds `WeightConfig` dataclasses:

```python
@dataclass
class WeightConfig:
    empathy: float
    clarity: float
    evidence: float
    actionability: float
    timing: float = 0.0
```

### Persona Weight Profiles (example)

| Persona | empathy | clarity | evidence | actionability |
|---------|---------|---------|----------|---------------|
| `elderly` | High | High | Medium | Medium |
| `overconfident` | Low | Medium | High | High |
| `student` | Medium | High | Medium | High |

Weights are applied when calculating per-round trust changes, making the trust system more nuanced than a flat delta.

---

## 13. Scammer Strategy Management

### What It Does

Tracks which scam tactics the ScammerAgent has used across rounds, detecting repetition fatigue and suggesting strategy shifts to keep the simulation realistic.

### Implementation

**File**: `backend/utils/scammer_strategy_manager.py`

- Maintains a per-session log of tactics used (e.g. authority_claim, urgency, social_proof).
- Calculates **fatigue multiplier** based on repetition count (−10% to −50%).
- Provides `get_next_strategy()` to suggest the next unused or least-used tactic.
- Feeds into trust change calculation in `performance_tracker.py`.

### Tactic Categories (from `config.py` → `ScamTacticsConfig`)

| Category | Examples |
|----------|----------|
| Authority | Impersonation of police, bank, government |
| Urgency | "Account frozen", "Act now", time pressure |
| Social proof | Fake testimonials, referrals |
| Reciprocity | Free gifts, trial offers |
| Scarcity | Limited slots, exclusive access |
| Fear | Legal threats, arrest warrants |

---

## Additional Utility Modules Reference

| Module | Purpose |
|--------|---------|
| `utils/role_enforcer.py` | Prevents agents from breaking character mid-conversation |
| `utils/role_consistency_checker.py` | Validates agent responses stay in-role |
| `utils/context_manager.py` | Sliding window for conversation history (last 10 turns) |
| `utils/conversation_summarizer.py` | Summarises long conversations for context injection |
| `utils/hybrid_evaluation.py` | Combines rule-based + AI semantic evaluation of responses |
| `utils/chain_of_thought.py` | Chain-of-thought prompting helper for complex reasoning |
| `utils/ai_judgment_optimizer.py` | Optimises AI judgment calls for trust delta calculation |
| `utils/gemini_metrics.py` | Tracks Gemini API usage, latency, token counts |
| `utils/prompt_monitor.py` | Monitors prompt quality and flags regressions |
| `utils/victim_response_analyzer.py` | Analyses victim responses for emotional state detection |
| `utils/learning_curve_tracker.py` | Tracks player improvement over multiple sessions |
| `utils/finetuning_formatter.py` | Formats training data for Ollama fine-tuning |
| `utils/multilingual_prompts.py` | Prompt templates in Cantonese/Mandarin/English |
| `utils/rewrite_context_injector.py` | Injects rewrite hints into agent context |
