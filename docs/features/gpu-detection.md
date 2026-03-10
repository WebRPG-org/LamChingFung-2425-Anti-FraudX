# Feature: GPU Detection

> Category: Secondary | Version: 4.1 | Last Updated: 2026-03-11

---

## Overview

At startup, the backend detects whether an NVIDIA GPU is available and logs the result. In strict mode (`FORCE_GPU=1`), the server refuses to start without a GPU — ensuring Ollama always runs with acceleration.

---

## Implementation

File: `backend/utils/gpu_checker.py`

```python
def check_and_enforce_gpu() -> bool:
    # Runs: nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
    # Returns True if GPU found, False otherwise
    # If FORCE_GPU=1 and no GPU: sys.exit(1)
```

Called from `main.py` during startup, before any router registration.

---

## Behaviour by Config

| `FORCE_GPU` value | GPU found | Behaviour |
|-------------------|-----------|----------|
| `0` (default) | Yes | Logs GPU name + VRAM, continues |
| `0` (default) | No | Logs warning, continues (CPU mode) |
| `1` | Yes | Logs GPU info, continues |
| `1` | No | Logs error, `sys.exit(1)` |

---

## Notes

- `gpu_status.json` is **not** cached between runs — detection executes fresh on every startup
- Only detects NVIDIA GPUs via `nvidia-smi`; AMD/Intel GPUs are not detected
- Ollama uses the detected GPU automatically — no additional config needed

---

## Relevant Files

```
backend/utils/gpu_checker.py   check_and_enforce_gpu()
backend/main.py                Calls gpu_checker at startup
backend/.env                   FORCE_GPU=0 (default)
```

---

## Related Features

- [llm-backend.md](llm-backend.md) — Ollama benefits from GPU acceleration
