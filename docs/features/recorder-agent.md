# Feature: RecorderAgent Analysis

> Category: Secondary | Version: 4.1 | Last Updated: 2026-03-11

---

## Overview

At the end of every battle session (win, loss, or draw), `RecorderAgent` generates a **structured post-game analysis report**. The report educates the player on what happened, which tactics were used, and how to better protect themselves.

---

## When It Runs

- Triggered after `game_over = True` is set in `GameSession`
- Called from `rpgv2_game_modes_routes.py` after outcome is determined
- In auto-mode: called by `SimulationRunner` at simulation end
- Result displayed in `ResultScene.ts`

---

## Input: `GameSession.round_logs`

`RecorderAgent` receives the full `round_logs` list from `GameSession`:

```python
round_logs = [
    {
        "round": 1,
        "player_message": "你係邊間銀行?",
        "scammer_response": "我係恆生銀行...",
        "expert_response": "請注意...",
        "trust_before": {"scammer": 50, "expert": 50, "alertness": 40},
        "trust_after":  {"scammer": 55, "expert": 47, "alertness": 42},
        "emotional_state": "neutral",
        "tactic_used": "authority_claim"
    },
    ...
]
```

---

## Report Contents

| Section | Description |
|---------|-------------|
| Outcome | `scammer_win` / `expert_win` / `victim_self_protect` / `draw` |
| Tactics identified | List of scam tactics detected across all rounds |
| Key decision moments | Rounds where trust changed most significantly |
| Educational recommendations | Specific advice based on how the player responded |
| Trust progression | Per-round trust values (used for chart in ResultScene) |
| Scores | `player_score`, `ai_score` |

---

## Prompt Design

File: `backend/agents/recorder.py`

The RecorderAgent system prompt instructs the LLM to:
- Act as a neutral educational analyst
- Identify scam tactic categories from the conversation
- Highlight moments where the victim was most vulnerable
- Provide actionable advice in plain Cantonese
- Keep the report structured (JSON-serialisable sections)

---

## Frontend Display

File: `rpg-platform-v2/src/scenes/ResultScene.ts`

- Rendered after `BattleScene` closes
- Shows outcome badge, tactic list, trust progression chart, and recommendations
- "Play Again" button clears `sessionStorage` and returns to `WorldMapScene`

---

## Relevant Files

```
backend/agents/recorder.py                    RecorderAgent class + prompt
backend/utils/rpgv2_game_mode_manager.py      GameSession.round_logs accumulation
backend/api/rpgv2_game_modes_routes.py        Triggers RecorderAgent on game_over
backend/services/simulation_runner.py         Triggers RecorderAgent in auto-mode
rpg-platform-v2/src/scenes/ResultScene.ts     Displays report
```

---

## Related Features

- [multi-agent-system.md](multi-agent-system.md) — RecorderAgent is the 4th agent
- [trust-meter.md](trust-meter.md) — round_logs include per-round trust deltas
- [auto-mode.md](auto-mode.md) — Auto-mode also triggers RecorderAgent
- [battle-scene.md](battle-scene.md) — Outcome detection triggers Recorder
