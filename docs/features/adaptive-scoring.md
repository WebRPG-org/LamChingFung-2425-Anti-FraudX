# Feature: Adaptive Scoring System

> Category: Secondary | Version: 4.1 | Last Updated: 2026-03-11

---

## Overview

Instead of applying fixed trust deltas per round, the Adaptive Scoring System **adjusts evaluation weights based on the victim's persona**. An elderly victim is more affected by empathetic appeals; an overconfident victim responds more to hard evidence. This makes the simulation more realistic and psychologically grounded.

---

## Implementation

File: `backend/utils/adaptive_scoring.py`

### WeightConfig

```python
@dataclass
class WeightConfig:
    empathy: float        # How much empathetic language affects trust
    clarity: float        # How much clear, simple explanation affects trust
    evidence: float       # How much factual evidence/citations affect trust
    actionability: float  # How much actionable advice affects trust
    timing: float = 0.0   # Bonus for well-timed intervention
```

### AdaptiveWeightOptimizer

```python
class AdaptiveWeightOptimizer:
    def get_weights(self, persona: str) -> WeightConfig:
        # Returns persona-specific WeightConfig
        ...

    def apply_weights(self, raw_score: float, response_features: dict, persona: str) -> float:
        # Applies weights to raw trust delta
        ...
```

---

## Persona Weight Profiles

| Persona | empathy | clarity | evidence | actionability | Notes |
|---------|---------|---------|----------|---------------|-------|
| `elderly` | 0.40 | 0.35 | 0.15 | 0.10 | Emotional appeals most effective |
| `average` | 0.25 | 0.25 | 0.25 | 0.25 | Balanced |
| `overconfident` | 0.10 | 0.20 | 0.45 | 0.25 | Needs hard facts to change mind |
| `student` | 0.20 | 0.35 | 0.25 | 0.20 | Responds to clear explanations |

---

## Integration with Trust System

```
Agent response received
  │
  ▼
Response features extracted
  (empathy_score, clarity_score, evidence_score, actionability_score)
  │
  ▼
AdaptiveWeightOptimizer.apply_weights(raw_delta, features, persona)
  │
  ▼
Adjusted trust delta applied to VictimTrustState
```

This runs inside the trust update pipeline in `performance_tracker.py`.

---

## Relevant Files

```
backend/utils/adaptive_scoring.py       AdaptiveWeightOptimizer + WeightConfig
backend/utils/performance_tracker.py    Calls adaptive scoring in trust update
backend/config.py                       PersonaConfig (persona definitions)
```

---

## Related Features

- [trust-meter.md](trust-meter.md) — Trust system that uses adaptive weights
- [multi-agent-system.md](multi-agent-system.md) — Persona selection at session start
