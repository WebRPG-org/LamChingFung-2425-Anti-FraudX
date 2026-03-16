# Feature: Scammer Strategy Management

> Category: Secondary | Version: 4.1 | Last Updated: 2026-03-11

---

## Overview

Tracks which scam tactics the `ScammerAgent` has deployed across rounds and detects **repetition fatigue** — the natural drop in effectiveness when the same tactic is used repeatedly. Also suggests the next optimal tactic to keep the simulation realistic and varied.

---

## Implementation

File: `backend/utils/scammer_strategy_manager.py`

### Core Responsibilities

| Function | Description |
|----------|-------------|
| Track tactic usage | Records every tactic used per session with round number |
| Calculate fatigue multiplier | Returns effectiveness reduction based on repetition count |
| Suggest next strategy | Returns least-recently-used or unused tactic |
| Feed trust pipeline | Fatigue multiplier applied before trust delta is calculated |

### Fatigue Multiplier

```python
def get_fatigue_multiplier(self, tactic: str) -> float:
    count = self.tactic_counts.get(tactic, 0)
    if count == 0:   return 1.00   # First use — full effect
    if count == 1:   return 0.90   # Second use — 10% reduction
    if count == 2:   return 0.70   # Third use  — 30% reduction
    return 0.50                    # 4th+ use    — 50% reduction
```

### Next Strategy Selection

```python
def get_next_strategy(self) -> str:
    # Returns tactic with lowest usage count
    # Prioritises completely unused tactics
    # Falls back to least-used if all have been used
```

---

## Tactic Categories

Defined in `backend/config.py` → `ScamTacticsConfig`:

| Tactic ID | Category | Real-world Example |
|-----------|----------|-------------------|
| `authority_claim` | Authority | "我係警察" / "我係銀行職員" |
| `urgency` | Urgency | "你帳戶即將被凍結" / "限時優惠" |
| `social_proof` | Social proof | 假冒朋友推薦 / 假見證 |
| `reciprocity` | Reciprocity | 免費試用 / 小禮物 |
| `scarcity` | Scarcity | "只剩最後3個名額" |
| `fear` | Fear | 假冒法院通知 / 逮捕令威脅 |
| `liking` | Rapport | 假裝共同興趣 / 情緣詐騙 |
| `commitment` | Commitment | 逐步升級承諾 |
| `information_gathering` | Reconnaissance | 問問題套取個人資料 |
| `financial_hook` | Financial | 保證高回報投資 |

---

## Integration with Trust Pipeline

```
ScammerAgent generates response
  │
  ▼
Tactic identified from response (keyword match or LLM classification)
  │
  ▼
ScammerStrategyManager.record_tactic(tactic)
ScammerStrategyManager.get_fatigue_multiplier(tactic)
  │
  ▼
Raw trust delta × fatigue_multiplier × emotional_multiplier
  │
  ▼
VictimTrustState.update(change_type, adjusted_delta, reason)
```

---

## Per-Session Isolation

Each `GameSession` has its own `ScammerStrategyManager` instance. Tactic counts reset to zero at session start — fatigue does not carry over between different players or sessions.

---

## Relevant Files

```
backend/utils/scammer_strategy_manager.py   Core tactic tracking + fatigue logic
backend/utils/performance_tracker.py        Applies fatigue multiplier in trust update
backend/config.py                           ScamTacticsConfig (tactic list)
backend/agents/scammer.py                   ScammerAgent that generates tactics
```

---

## Related Features

- [trust-meter.md](trust-meter.md) — Fatigue multiplier feeds into trust delta calculation
- [multi-agent-system.md](multi-agent-system.md) — ScammerAgent that this manages
- [adaptive-scoring.md](adaptive-scoring.md) — Other modifier in the same trust pipeline
- [recorder-agent.md](recorder-agent.md) — Tactic list appears in post-game report
