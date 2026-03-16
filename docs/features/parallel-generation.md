# Feature: Parallel Response Generation

> Category: Core | Version: 4.1 | Last Updated: 2026-03-11

---

## Overview

Instead of waiting for each AI agent to respond sequentially, the platform generates **all agent responses simultaneously** using Python's `asyncio.gather()`. This cuts total round-trip time by ~50% and is the single largest latency optimisation in the system.

---

## Implementation

File: `backend/api/rpgv2_game_modes_routes.py`

```python
# Before (sequential) — 8–16 seconds total
scammer_response = await scammer_agent.generate(message, history)
expert_response  = await expert_agent.generate(message, history)

# After (parallel) — 4–8 seconds total
scammer_response, expert_response = await asyncio.gather(
    scammer_agent.generate(message, history),
    expert_agent.generate(message, history)
)
```

---

## Per-Mode Parallelism

| Mode | Parallel tasks | Notes |
|------|---------------|-------|
| `three_way` | ScammerAgent + ExpertAgent | VictimAgent added if auto-mode active |
| `scammer_only` | ScammerAgent only | No gather needed; single await |
| `expert_only` | ExpertAgent only | No gather needed; single await |
| Auto simulation | Scammer + Expert + Victim | All three gathered simultaneously |

---

## Performance Benchmarks

| Scenario | Before optimisation | After optimisation | Improvement |
|----------|--------------------|--------------------|-------------|
| Ollama — first response (cold) | 10–15s | 3–6s | ~60% |
| Ollama — subsequent responses | 5–10s | 2–4s | ~50% |
| Gemini — single agent | 4–8s | 2–4s | ~40% |
| Gemini — Scammer + Expert parallel | 8–16s | 4–8s | ~50% |

Note: Ollama improvements also include shared HTTP client, reduced `num_ctx`, and warm-up (see [llm-backend.md](llm-backend.md)).

---

## Error Handling

`asyncio.gather()` is called with `return_exceptions=False` (default). If either agent raises an exception:
- The exception propagates and the route handler returns a 500 error
- The frontend displays a system error bubble
- Session state is preserved; player can retry the message

For resilience in auto-mode simulations, individual agent calls wrap exceptions and return a fallback string instead of raising.

---

## Why Not `asyncio.gather(return_exceptions=True)`?

In battle mode, a partial response (one agent succeeded, one failed) is worse UX than a clean error — the trust meter would update asymmetrically. A full retry is safer.

---

## Relevant Files

```
backend/api/rpgv2_game_modes_routes.py   asyncio.gather() implementation
backend/services/simulation_runner.py    Auto-mode 3-way parallel gather
backend/agents/scammer.py                ScammerAgent.generate()
backend/agents/expert.py                 ExpertAgent.generate()
backend/agents/victim.py                 VictimAgent.generate()
```

---

## Related Features

- [llm-backend.md](llm-backend.md) — Individual LLM optimisations that compound with parallelism
- [auto-mode.md](auto-mode.md) — Three-way parallel gather in simulation
- [battle-scene.md](battle-scene.md) — Frontend waits for parallel response before updating UI
