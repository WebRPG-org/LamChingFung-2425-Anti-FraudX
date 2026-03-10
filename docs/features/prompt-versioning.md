# Feature: Prompt Version Management

> Category: Secondary | Version: 4.1 | Last Updated: 2026-03-11

---

## Overview

Allows **A/B testing of different agent prompt versions** at runtime without restarting the server. Each version is registered with a unique ID, and the system tracks which version produces better trust outcomes.

---

## Architecture

```
main.py startup
  → register_initial_prompts(version_manager)    ← services/prompt_helper.py
  → PromptVersionManager initialized

Runtime:
  GET  /api/prompts/versions    → list all registered versions
  POST /api/prompts/switch      → switch active version for an agent
  GET  /api/prompts/compare     → compare performance across versions
```

---

## PromptVersionManager

File: `backend/utils/prompt_version_manager.py`

Key operations:

| Method | Purpose |
|--------|---------|
| `register(agent_type, version_id, prompt_text, description)` | Register a new prompt version |
| `get_active(agent_type)` | Return currently active prompt for an agent |
| `switch(agent_type, version_id)` | Switch active version |
| `compare(agent_type)` | Return performance metrics for all versions |
| `record_outcome(version_id, outcome)` | Log win/loss/draw for a version |

Version history is persisted to `backend/data/prompt_versions.json`.

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/prompts/versions` | List all registered versions with metadata |
| POST | `/api/prompts/switch` | `{ "agent_type": "scammer", "version_id": "v2" }` |
| GET | `/api/prompts/compare` | Performance metrics comparison across versions |

---

## Relevant Files

```
backend/utils/prompt_version_manager.py   Core versioning logic
backend/services/prompt_helper.py         Startup registration of initial versions
backend/api/prompt_version_routes.py      REST API
backend/data/prompt_versions.json         Persisted version history
```

---

## Related Features

- [multi-agent-system.md](multi-agent-system.md) — Agents that use versioned prompts
- [llm-backend.md](llm-backend.md) — LlmFactory applies active prompt version
