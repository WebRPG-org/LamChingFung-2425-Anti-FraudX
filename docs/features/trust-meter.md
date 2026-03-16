# Feature: Trust Meter System

> Category: Core | Version: 4.1 | Last Updated: 2026-03-11

---

## Overview

The Trust Meter tracks the **victim's psychological state** across three real-time dimensions. These values drive the outcome of every battle session — a scammer win, expert win, or victim self-protection. The system models realistic human behaviour: trust that has built up is hard to destroy, repeated tactics wear thin, and emotional states amplify or dampen persuasion.

---

## Trust Dimensions

| Dimension | Range | Meaning | Initial Value (varies by persona) |
|-----------|-------|---------|-----------------------------------|
| `scammer_trust` | 0–100 | How much the victim believes the scammer | 30–70 |
| `expert_trust` | 0–100 | How much the victim trusts the expert's advice | 40–60 |
| `alertness` | 0–100 | Victim's overall fraud suspicion level | 30–70 |

---

## State Object: `VictimTrustState`

File: `backend/utils/performance_tracker.py`

```python
@dataclass
class VictimTrustState:
    trust_in_scammer: int = 50
    trust_in_expert: int = 50
    alertness: int = 50
    emotional_state: str = "neutral"  # neutral | calm | anxious | panicked | suspicious
    history: List[Dict] = field(default_factory=list)

    def update(self, change_type: str, change_value: int, reason: str):
        # Clamps to 0–100, appends to history
        ...
```

The `history` list records every trust change with timestamp, type, value, and reason — used by `RecorderAgent` for post-game analysis.

---

## Session Object: `GameSession`

File: `backend/utils/rpgv2_game_mode_manager.py`

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
    start_time: str
    last_update: str
    game_over: bool = False
    winner: Optional[str] = None
    round_logs: List[Dict] = field(default_factory=list)
```

`round_logs` captures per-round detail (agent responses, trust deltas, emotional state) for the Recorder.

---

## Win/Loss Outcome Thresholds

Defined in `backend/config.py` → `TrustConfig`:

| Condition | Outcome | Winner |
|-----------|---------|--------|
| `scammer_trust >= 80` | Victim scammed | `"scammer"` |
| `expert_trust >= 75` | Victim protected | `"expert"` |
| `scammer_trust < 40` AND `expert_trust > 60` | Expert wins early | `"expert"` |
| `alertness >= 80` | Victim self-protects | `"victim"` |
| `round_count >= 15` | Max rounds reached | No winner (draw) |

Checked after every round in `rpgv2_game_modes_routes.py`.

---

## Trust Modifiers

### 1. Inertia
High existing trust is harder to move:

| Existing trust | Change multiplier |
|---------------|------------------|
| ≥ 80 | −40% to −50% |
| 50–79 | No adjustment |
| ≤ 20 | Slightly easier to change |

### 2. Tactic Fatigue
Repeated use of the same scam tactic loses effectiveness:

| Repetition count | Effectiveness multiplier |
|-----------------|-------------------------|
| 1st use | 100% |
| 2nd use | 90% |
| 3rd use | 70% |
| 4th+ use | 50% |

Managed by `ScammerStrategyManager` (`backend/utils/scammer_strategy_manager.py`).

### 3. Emotional State Multipliers

| Emotional State | Scammer effectiveness | Expert effectiveness |
|----------------|----------------------|---------------------|
| `anxious` | +30% | −20% |
| `panicked` | +50% | −40% |
| `suspicious` | −30% | +40% |
| `calm` | Baseline | Baseline |
| `neutral` | Baseline | Baseline |

### 4. Persona-Based Weight Adjustment
`AdaptiveWeightOptimizer` (`backend/utils/adaptive_scoring.py`) adjusts the weight of each evaluation dimension (empathy, clarity, evidence, actionability) based on victim persona. See [adaptive-scoring.md](adaptive-scoring.md).

---

## Frontend Components

| File | Purpose |
|------|---------|
| `rpg-platform-v2/src/systems/TrustSystem.ts` | Applies trust delta received from API to local state |
| `rpg-platform-v2/src/ui/TrustMeter.ts` | Renders animated progress bars in BattleScene sidebar |

The frontend trust state is **not authoritative** — it mirrors the backend `GameSession` values. On restore from `sessionStorage`, trust values are re-synced from saved state.

---

## Relevant Files

```
backend/utils/performance_tracker.py      VictimTrustState dataclass + update logic
backend/utils/rpgv2_game_mode_manager.py  GameSession dataclass + session store
backend/utils/adaptive_scoring.py         Persona-based weight adjustment
backend/utils/scammer_strategy_manager.py Tactic fatigue tracking
backend/config.py                         TrustConfig (thresholds, multipliers)
backend/api/rpgv2_game_modes_routes.py    Outcome checking per round
rpg-platform-v2/src/systems/TrustSystem.ts
rpg-platform-v2/src/ui/TrustMeter.ts
```

---

## Related Features

- [multi-agent-system.md](multi-agent-system.md) — Agents that affect trust
- [battle-scene.md](battle-scene.md) — Visual trust meter display
- [adaptive-scoring.md](adaptive-scoring.md) — Persona-based weight adjustments
- [scammer-strategy.md](scammer-strategy.md) — Tactic fatigue management
- [recorder-agent.md](recorder-agent.md) — Uses trust history for analysis
