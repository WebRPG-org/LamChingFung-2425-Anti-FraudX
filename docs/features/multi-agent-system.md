# Feature: Multi-Agent AI Dialogue System

> Category: Core | Version: 4.1 | Last Updated: 2026-03-11

---

## Overview

The platform simulates realistic fraud scenarios using **four specialised AI agents** operating simultaneously. Each agent has a distinct role, persona, and system prompt grounded in 281 real Hong Kong scam cases documented by ADCC.

---

## Agents

| Agent | Class | Role | Persona |
|-------|-------|------|---------|
| Scammer | `ScammerAgent` | Plays the fraudster; applies real HK tactics to gain victim trust | Professional scammer, adaptive, escalating pressure |
| Expert | `ExpertAgent` | Anti-fraud advisor; warns, educates, provides evidence | Calm, authoritative, evidence-based |
| Victim | `VictimAgent` | Simulates victim reactions (auto mode only) | Varies by persona type |
| Recorder | `RecorderAgent` | Analyses the completed session; generates post-game report | Neutral analyst |

---

## Architecture

```
Player message
    │
    ▼
rpgv2_game_modes_routes.py
    │
    ├── asyncio.gather()
    │     ├── ScammerAgent.generate(player_message, history, scam_type)
    │     └── ExpertAgent.generate(player_message, history, scam_type)
    │
    ▼
LlmFactory.create_llm(agent_type)
    │
    ├── GEMINI_ENABLED=true  → GeminiLlm
    └── GEMINI_ENABLED=false → OllamaLlm
```

---

## Initialisation Flow

1. `LlmFactory.create_llm(agent_type, scam_type)` is called per request.
2. RAG context (top-3 relevant HK cases from ChromaDB) is fetched and appended to `system_instruction`.
3. Few-shot examples from `prompts/scammer_examples.py` / `expert_examples.py` are prepended.
4. Agent object is created with the enriched prompt and calls the underlying LLM.

---

## System Instructions (`system_instructions.py`)

Each agent's base prompt is stored here. The Scammer prompt embeds **4 fraud category templates** drawn from real cases:

| Category | Real Case Count | Opening Template |
|----------|----------------|------------------|
| Impersonation (官員) | 71 | "你好，我係香港警務處反詐騙組嘅警員..." |
| Bank (銀行) | 172 | "你好，我係XX銀行客戶服務部..." |
| Investment (投資) | 15 | "你好，我係XX投資公司嘅理財顧問..." |
| Online Shopping (網購) | 4 | "你好，我係賣家，有你想要嘅貨品..." |

The Expert prompt instructs the agent to:
- Identify the scam type from context
- Cite real ADCC/HK police hotline references
- Keep responses under 100 characters (enforced by `role_enforcer.py`)

---

## Victim Personas

Defined in `backend/config.py` (`PersonaConfig`). Controls starting trust values.

| Persona | scammer_trust | expert_trust | alertness | Description |
|---------|--------------|--------------|-----------|-------------|
| `elderly` | 70 | 50 | 30 | Trusts authority figures, most vulnerable |
| `average` | 50 | 60 | 50 | Balanced, moderate scepticism |
| `overconfident` | 30 | 40 | 70 | Overestimates own fraud awareness |
| `student` | 55 | 45 | 45 | Curious, moderate risk |

`AdaptiveWeightOptimizer` further adjusts evaluation weights per persona at runtime (see `adaptive-scoring.md`).

---

## Relevant Files

```
backend/agents/
  scammer.py                ScammerAgent class
  expert.py                 ExpertAgent class
  victim.py                 VictimAgent class
  recorder.py               RecorderAgent class
  base_agent.py             BaseAntifraudAgent (shared ADK base)
  system_instructions.py    Per-agent system prompts
  hk_organizations.py       HK hotline / org reference data
  scam_knowledge_base.json  281 structured HK scam cases
  few_shot_examples.json    JSON store of few-shot examples
  prompts/
    prompt_builder.py       Assembles final prompt (RAG + examples + instructions)
    scammer_examples.py     Few-shot examples for ScammerAgent
    expert_examples.py      Few-shot examples for ExpertAgent
    victim_examples.py      Few-shot examples for VictimAgent
```

---

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| ADK `BaseLlm` base class | Enables drop-in swap between Ollama and Gemini without changing agent code |
| RAG injection per request | Ensures scam type-specific real cases are always used |
| Few-shot examples in Python files | Easier to version-control and A/B test than JSON |
| Recorder runs post-session only | Avoids adding latency to real-time battle loop |
| `base_agent.py` shared base | Eliminates duplicated init/generate boilerplate across 4 agents |

---

## Related Features

- [llm-backend.md](llm-backend.md) — How agents call the LLM
- [rag-knowledge-base.md](rag-knowledge-base.md) — How real HK cases are injected
- [trust-meter.md](trust-meter.md) — How agent responses affect trust scores
- [recorder-agent.md](recorder-agent.md) — Post-session analysis report
- [auto-mode.md](auto-mode.md) — VictimAgent in fully automated simulation
