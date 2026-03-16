# AI Anti-Fraud Platform — Core Features

> Version: 4.1 | Last Updated: 2026-03-11

This document describes the **primary features** of the platform — the features that define its core value proposition.

---

## Table of Contents

1. [Multi-Agent AI Dialogue System](#1-multi-agent-ai-dialogue-system)
2. [Dual LLM Backend (Ollama + Gemini)](#2-dual-llm-backend-ollama--gemini)
3. [RPGv2 Battle Scene (Overlay Mode)](#3-rpgv2-battle-scene-overlay-mode)
4. [Trust Meter System](#4-trust-meter-system)
5. [Parallel Response Generation](#5-parallel-response-generation)

---

## 1. Multi-Agent AI Dialogue System

### What It Does

Simulates a realistic fraud scenario with **four AI agents** playing different roles:

| Agent | Role | Persona | File |
|-------|------|---------|------|
| `ScammerAgent` | Plays the fraudster; uses real HK tactics from 281 cases | Professional scammer | `backend/agents/scammer.py` |
| `ExpertAgent` | Plays the anti-fraud expert; warns and educates | Calm, evidence-based advisor | `backend/agents/expert.py` |
| `VictimAgent` | Simulates victim reactions (auto mode) | Varies by persona type | `backend/agents/victim.py` |
| `RecorderAgent` | Analyses session and generates post-game report | Neutral analyst | `backend/agents/recorder.py` |

### How It Works

1. **Initialization**: Each agent is created via `LlmFactory.create_llm(agent_type)`, selecting Ollama or Gemini based on `GEMINI_ENABLED` env var.
2. **Prompt Construction**: `agents/prompts/prompt_builder.py` builds role-specific system instructions. Scammer/Expert prompts include real HK scam case examples injected via RAG.
3. **System Instructions**: `system_instructions.py` stores per-agent prompts. Scammer prompt references **4 fraud categories** (impersonation 71 cases, bank 172 cases, investment 15 cases, online shopping 4 cases) drawn from the 281-case knowledge base.
4. **ADK Integration**: All agents extend `google.adk.agents.Agent` (via `BaseLlm`). `llm_utils.py` provides the shared `extract_text_from_contents()` helper used by both OllamaLlm and GeminiLlm.

### Relevant Files

```
backend/agents/
  scammer.py              ScammerAgent
  expert.py               ExpertAgent
  victim.py               VictimAgent
  recorder.py             RecorderAgent
  base_agent.py           BaseAntifraudAgent (shared base)
  system_instructions.py  Per-agent system prompts
  prompts/
    prompt_builder.py     Builds final prompts (RAG + examples + instructions)
    scammer_examples.py   Few-shot examples for scammer
    expert_examples.py    Few-shot examples for expert
    victim_examples.py    Few-shot examples for victim
  few_shot_examples.json  JSON store of few-shot examples
  scam_knowledge_base.json  281 structured real HK scam cases
  hk_organizations.py     HK hotlines and org reference data
```

### Persona Types

Victim persona affects initial trust values and susceptibility:

| Persona | Trust in Scammer | Trust in Expert | Alertness | Description |
|---------|-----------------|-----------------|-----------|-------------|
| `elderly` | 70 | 50 | 30 | Trusts authority, vulnerable |
| `average` | 50 | 60 | 50 | Balanced, moderate skepticism |
| `overconfident` | 30 | 40 | 70 | Overestimates own judgment |
| `student` | 55 | 45 | 45 | Curious, moderate risk |

Defined in `backend/config.py` (`PersonaConfig`). `AdaptiveWeightOptimizer` (`backend/utils/adaptive_scoring.py`) further adjusts per-agent evaluation weights based on persona at runtime.

---

## 2. Dual LLM Backend (Ollama + Gemini)

### What It Does

Provides a **provider-agnostic LLM layer** switchable between local Ollama and cloud Gemini at runtime — no code changes needed.

### Architecture

```
LlmFactory.create_llm(agent_type)
  │
  ├── GEMINI_ENABLED=true  →  GeminiLlm  →  Google Gemini API
  └── GEMINI_ENABLED=false →  OllamaLlm  →  Ollama (local, port 11434)
```

> **Note**: `GEMINI_ENABLED` is read from `backend/.env`. Do **not** wrap the value in quotes (e.g. use `GEMINI_ENABLED=true`, not `GEMINI_ENABLED='true'`).

### OllamaLlm (`backend/llms/ollama_llm.py`)

Extends `google.adk.models.BaseLlm`. Sends prompts to Ollama's `/api/generate` endpoint.

**Key optimizations:**

| Optimization | Before | After | Impact |
|-------------|--------|-------|--------|
| Shared HTTP client | New client per request | Singleton `_shared_client` with connection pooling | −0.5s/call |
| Context window | `num_ctx=4096` | `num_ctx=2048` | −2–5s |
| Max output tokens | `num_predict=2000` | `num_predict=400` | −2–8s |
| Auto-pull on request | Blocks 3–10s | Removed; startup warm-up only | −3–10s |
| History truncation | Unlimited | Last 10 turns | −1–3s |
| Retry delay | 1s, 2s, 4s | 0.5s, 1s | −3–7s on failure |

**Key methods:**

| Method | Purpose |
|--------|---------|
| `_get_shared_client(base_url)` | Singleton `httpx.AsyncClient` with keep-alive pooling |
| `_extract_text_from_contents(contents)` | Now delegates to `llm_utils.extract_text_from_contents()` (DUP-001 fix) |
| `generate_content_async()` | Main generation method; truncates overly long responses at sentence boundaries |
| `warm_up_model()` | Sends 1-token request to pre-load model into GPU memory |

### GeminiLlm (`backend/llms/gemini_llm.py`)

Extends `google.adk.models.BaseLlm`. Uses `google.genai` SDK with streaming.

**Key configuration (from `__init__`):**

```python
max_output_tokens: int = 800   # Optimised from 2048
timeout: float = 45.0          # Reduced from 60s
max_retries: int = 2           # Reduced from 3
temperature: float = 0.7
```

**Key methods:**

| Method | Purpose |
|--------|---------|
| `_generate_with_stream(prompt)` | Calls `generate_content_stream`, collects chunks, joins to final text |
| `_retry_with_backoff(func)` | Exponential backoff for 429/503/timeout errors |
| `_get_generation_config()` | Returns `GenerateContentConfig` with all params |
| `_get_safety_settings()` | Disables all safety filters (required for scam simulation) |

**Shared utility:**

`backend/llms/llm_utils.py` — `extract_text_from_contents()` shared by both adapters (DUP-001 fix; previously duplicated).

### LlmFactory (`backend/llms/llm_factory.py`)

Static factory. Reads `GEMINI_ENABLED` from config, returns appropriate LLM. Also injects RAG context into system instructions.

| Method | Purpose |
|--------|---------|
| `create_llm(agent_type, scam_type, context)` | Main entry point |
| `get_rag_context(scam_type, context)` | Queries ChromaDB for relevant HK cases |
| `get_current_provider()` | Returns `'gemini'` or `'ollama'` |
| `validate_gemini_config()` | Checks API key and model IDs |

### Runtime Model Switching

`POST /api/model/switch` (`model_switch_routes.py`) allows switching provider without restart. Config is reflected immediately in subsequent `LlmFactory.create_llm()` calls.

---

## 3. RPGv2 Battle Scene (Overlay Mode)

### What It Does

Provides an **immersive in-game battle UI** that overlays the 2D world map. Players interact with AI agents via chat bubbles, voice input, and a live trust meter.

### Architecture

```
WorldMapScene (Phaser, running)
  Player touches NPC
  scene.launch('BattleScene')   ← map stays alive, not destroyed
  scene.pause('WorldMapScene')
    │
    ▼
BattleScene HTML overlay (z-index: 900)
  ├── rgba(10,14,39,0.75) background + backdrop-filter:blur(6px)
  ├── Chat bubble area  (left=AI, right=player, center=system)
  ├── Trust meter sidebar
  ├── Voice input (Web Speech API, zh-HK)
  └── Text input + send button
    │
  Player presses ESC / clicks "Return to Map"
  scene.stop('BattleScene')
  scene.resume('WorldMapScene')  ← resumes exactly where left off
```

### Key Implementation Details — `BattleScene.ts`

| Feature | Implementation |
|---------|---------------|
| HTML overlay | `document.createElement` injected into `#game-container` |
| CSS injection | Single `<style id="bo-css">` tag; injected once per page load |
| Chat bubbles | Left=AI, right=player, center=system messages |
| Typing indicator | Three-dot bounce animation while AI processes |
| Voice input | `window.SpeechRecognition`, 2s silence auto-stop, `zh-HK` locale |
| Session persistence | `sessionStorage` — `session_id`, messages, trust values, round count |
| State restoration | `tryRestoreState()` on `create()` — restores if same `scamType` |
| Keyboard shortcuts | `F1/F2/F3` = switch active AI; `ESC` = return to map |
| Trust meter | Animated progress bars, color gradients, hidden on mobile |

### API Endpoint

**POST** `/api/rpgv2/game-modes/chat` (`rpgv2_game_modes_routes.py`)

**Request:**
```json
{
  "session_id": "uuid",
  "player_message": "string",
  "scam_type": "investment|phishing|romance|...",
  "mode": "scammer_only|expert_only|three_way",
  "trust_data": { "scammer": 50, "expert": 60, "alertness": 40 }
}
```

**Response:**
```json
{
  "scammer_response": "string",
  "expert_response": "string",
  "trust_changes": { "scammer": 5, "expert": -3, "alertness": 2 },
  "round": 3,
  "outcome": null
}
```

---

## 4. Trust Meter System

### What It Does

Tracks the **victim's trust levels** across three dimensions in real-time, driving the outcome of each scenario.

### Trust Dimensions

| Dimension | Range | Meaning |
|-----------|-------|--------|
| `scammer_trust` | 0–100 | How much the victim believes the scammer |
| `expert_trust` | 0–100 | How much the victim trusts the expert's warnings |
| `alertness` | 0–100 | Victim's overall suspicion level |

### State Management

`VictimTrustState` dataclass (`backend/utils/performance_tracker.py`) manages all trust state:

```python
@dataclass
class VictimTrustState:
    trust_in_scammer: int = 50
    trust_in_expert: int = 50
    alertness: int = 50
    emotional_state: str = "neutral"  # calm/anxious/panicked/suspicious
    history: List[Dict] = field(default_factory=list)
```

`update(change_type, change_value, reason)` clamps values to 0–100 and appends to history.

### Session Management

`RPGv2GameModeManager` (`backend/utils/rpgv2_game_mode_manager.py`) manages `GameSession` dataclasses:

```python
@dataclass
class GameSession:
    session_id: str
    mode: GameMode           # "victim" | "expert" | "scammer" | "auto"
    scam_type: str
    victim_persona: str
    conversation_history: List[Dict]
    round_count: int
    trust_in_scammer: float
    trust_in_expert: float
    alertness: float
    player_score: int
    ai_score: int
    game_over: bool = False
    winner: Optional[str] = None
    round_logs: List[Dict] = field(default_factory=list)
```

### Outcome Thresholds (`config.py` → `TrustConfig`)

| Condition | Outcome |
|-----------|--------|
| `scammer_trust >= 80` | Scammer wins (victim scammed) |
| `expert_trust >= 75` | Expert wins (victim protected) |
| `scammer_trust < 40` AND `expert_trust > 60` | Expert wins |
| `alertness >= 80` | Victim self-protects |

### Trust Modifiers

Trust changes per round are affected by:

- **Inertia**: High existing trust (≥80) is harder to change further (−40% to −50% multiplier)
- **Fatigue**: Repeated tactics lose effectiveness (−10% to −50% based on repetition count)
- **Emotional state**: Victim's state (anxious/calm/suspicious/panicked) boosts or penalises each agent ±20–50%
- **Persona-based weights**: `AdaptiveWeightOptimizer` (`backend/utils/adaptive_scoring.py`) adjusts weights per persona (e.g. `elderly` gives more weight to empathy, `overconfident` weights evidence higher)

**Backend files**: `backend/utils/performance_tracker.py`, `backend/utils/adaptive_scoring.py`, `backend/config.py`
**Frontend files**: `rpg-platform-v2/src/systems/TrustSystem.ts`, `rpg-platform-v2/src/ui/TrustMeter.ts`

---

## 5. Parallel Response Generation

### What It Does

Generates responses from multiple AI agents **simultaneously**, cutting total response time by ~50%.

### Implementation

**File**: `backend/api/rpgv2_game_modes_routes.py`

```python
# Sequential (old): 8–16 seconds
scammer_response = await scammer_agent.generate(...)
expert_response  = await expert_agent.generate(...)

# Parallel (current): 4–8 seconds
scammer_response, expert_response = await asyncio.gather(
    scammer_agent.generate(...),
    expert_agent.generate(...)
)
```

All three game modes use parallel generation:

| Mode | Agents in parallel |
|------|--------------------|
| `three_way` | ScammerAgent + ExpertAgent + (optionally VictimAgent) |
| `scammer_only` | ScammerAgent only |
| `expert_only` | ExpertAgent only |

### Performance Results

| Scenario | Before | After | Improvement |
|----------|--------|-------|-------------|
| Ollama first response (with warm-up) | 10–15s | 3–6s | ~60% |
| Ollama subsequent responses | 5–10s | 2–4s | ~50% |
| Gemini single response (streaming) | 4–8s | 2–4s | ~40% |
| Scammer + Expert parallel | 8–16s | 4–8s | ~50% |
