# Feature: Model Switch API

> Category: Secondary | Version: 4.1 | Last Updated: 2026-03-11

---

## Overview

Allows **runtime switching between Ollama and Gemini** without restarting the backend server. The active provider is reflected immediately in all subsequent LLM calls.

---

## API Endpoints

File: `backend/api/model_switch_routes.py`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/model/current` | Get current provider name and active model info |
| POST | `/api/model/switch` | Switch provider (`{"provider": "gemini"}` or `{"provider": "ollama"}`) |
| GET | `/api/model/validate` | Validate current provider config (API key, reachability) |
| GET | `/api/model/config` | Full config dump — model names, token limits, URLs |

---

## How Switching Works

1. `POST /api/model/switch` updates the `GEMINI_ENABLED` runtime flag in `LlmFactory`.
2. No server restart needed — the flag is read on every `create_llm()` call.
3. Per-agent model overrides (e.g. `GEMINI_MODEL_SCAMMER`) remain unchanged.
4. The frontend dashboard (`frontend/index.html`) shows the current provider status.

---

## LlmFactory Methods Used

| Method | Purpose |
|--------|---------|
| `get_current_provider()` | Returns `'gemini'` or `'ollama'` |
| `get_provider_info()` | Returns dict: provider name, model IDs, token limits, base URL |
| `validate_gemini_config()` | Checks `GEMINI_API_KEY` is set and models are valid |

---

## Relevant Files

```
backend/api/model_switch_routes.py   REST API endpoints
backend/llms/llm_factory.py          get_current_provider(), get_provider_info()
backend/.env                         GEMINI_ENABLED, model name overrides
```

---

## Related Features

- [llm-backend.md](llm-backend.md) — Ollama and Gemini adapter details
- [tools-center.md](tools-center.md) — Creates custom Ollama models to switch to
