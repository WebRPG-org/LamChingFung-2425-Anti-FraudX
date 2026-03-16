# Feature: Offline Mode Checks

> Category: Secondary | Version: 4.1 | Last Updated: 2026-03-11

---

## Overview

When running with Ollama (local mode), the platform performs startup checks to verify that **no data leaves the local network**. This is critical for deployments where patient data or sensitive conversation content must remain on-device.

---

## Checks Performed

File: `backend/utils/offline_mode.py`

| Function | What It Checks |
|----------|---------------|
| `check_offline_mode()` | Verifies `GEMINI_ENABLED=false` |
| `check_data_isolation()` | Confirms no external API keys are configured |
| `verify_ollama_local_only()` | Confirms `OLLAMA_BASE_URL` points to `localhost` or `127.0.0.1` |

All three are called from `main.py` at startup:

```python
check_offline_mode()
check_data_isolation()
verify_ollama_local_only()
```

Failures log a warning but do **not** stop the server (non-fatal by design).

---

## When Checks Are Skipped

When `GEMINI_ENABLED=true`, these checks are skipped entirely — data is intentionally sent to the Google Gemini API and the offline guarantee does not apply.

---

## Relevant Files

```
backend/utils/offline_mode.py   All three check functions
backend/main.py                 Calls checks at startup
backend/.env                    GEMINI_ENABLED, OLLAMA_BASE_URL
```

---

## Related Features

- [llm-backend.md](llm-backend.md) — Ollama local adapter (the mode this protects)
- [gpu-detection.md](gpu-detection.md) — Also runs at startup alongside offline checks
