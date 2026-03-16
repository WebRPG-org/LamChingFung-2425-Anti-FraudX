# Feature: Auto Mode (Simulation)

> Category: Secondary | Version: 4.1 | Last Updated: 2026-03-11

---

## Overview

Runs a **fully automated AI-vs-AI simulation** with no human player input. All three agents (Scammer, Expert, Victim) respond autonomously. Used for training data generation, regression testing, and demonstration purposes.

---

## Flow

```
AutoModeScene.ts
  │
  │  WebSocket connect to /ws/simulate
  ▼
SimulationRunner.run_simulation(config)
  │
  │  For each round (max 15):
  │    asyncio.gather(
  │      ScammerAgent.generate(victim_last_message),
  │      ExpertAgent.generate(victim_last_message),
  │      VictimAgent.generate(scammer_response + expert_response)
  │    )
  │    → Update trust values
  │    → Check outcome
  │    → Broadcast round event via WebSocket
  │
  │  On outcome or max rounds:
  │    → RecorderAgent.analyse(session)
  │    → Broadcast final result
  ▼
AutoModeScene receives events, renders live simulation
```

---

## WebSocket Events

All events sent from backend to frontend over `/ws/simulate`:

| Event type | Payload | Description |
|------------|---------|-------------|
| `round_start` | `{ round: number }` | New round beginning |
| `agent_response` | `{ agent, text, trust_changes }` | Single agent response |
| `trust_update` | `{ scammer, expert, alertness }` | Updated trust values |
| `outcome` | `{ winner, reason }` | Simulation ended |
| `report` | `{ analysis: string }` | RecorderAgent report |

---

## Configuration

```python
# SimulationRunner accepts:
config = {
    "scam_type": "investment",
    "victim_persona": "elderly",
    "max_rounds": 15,
    "mode": "auto"
}
```

---

## Use Cases

| Use Case | How |
|----------|-----|
| Training data generation | Run many simulations; conversations saved as JSONL for fine-tuning |
| Regression testing | Verify trust outcome logic after code changes |
| Demo / presentation | Show live AI conversation without requiring a human player |
| Prompt evaluation | Compare prompt versions by running simulations with each |

---

## Relevant Files

```
rpg-platform-v2/src/scenes/AutoModeScene.ts   Frontend WebSocket client + live display
backend/api/simulation_routes.py               WebSocket endpoint /ws/simulate
backend/services/simulation_runner.py          Core simulation loop
backend/agents/victim.py                       VictimAgent (auto-responds)
```

---

## Related Features

- [multi-agent-system.md](multi-agent-system.md) — All three agents used simultaneously
- [parallel-generation.md](parallel-generation.md) — Three-way asyncio.gather
- [recorder-agent.md](recorder-agent.md) — Post-simulation analysis
- [tools-center.md](tools-center.md) — Fine-tune data generated from auto-mode runs
