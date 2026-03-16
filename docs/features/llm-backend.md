# Feature: Dual LLM Backend (Ollama + Gemini)

> Category: Core | Version: 4.1 | Last Updated: 2026-03-11

---

## Overview

A **provider-agnostic LLM abstraction layer** that switches between a locally-running Ollama instance and the Google Gemini cloud API. The switch is controlled by a single env var (`GEMINI_ENABLED`) and takes effect without restarting the server.

---

## Provider Selection

```
LlmFactory.create_llm(agent_type)
  │
  ├── GEMINI_ENABLED=true  →  GeminiLlm  →  Google Gemini API (cloud)
  └── GEMINI_ENABLED=false →  OllamaLlm  →  http://localhost:11434 (local)
```

> **Critical**: Set in `backend/.env`. Do NOT wrap in quotes.
> Correct:   `GEMINI_ENABLED=true`
> Incorrect: `GEMINI_ENABLED='true'`  ← Python reads the quotes as part of the value

---

## OllamaLlm (`backend/llms/ollama_llm.py`)

### What It Does

Extends `google.adk.models.BaseLlm`. Sends prompts to Ollama's `/api/generate` REST endpoint over HTTP using a shared async client.

### Performance Optimisations Applied

| Optimisation | Before | After | Latency Saved |
|-------------|--------|-------|---------------|
| HTTP client | New `httpx.AsyncClient` per request | Singleton `_shared_client` with connection pooling | −0.5s/call |
| Context window | `num_ctx=4096` | `num_ctx=2048` | −2–5s |
| Max output tokens | `num_predict=2000` | `num_predict=400` | −2–8s |
| Model auto-pull | Runs on every request (blocks 3–10s) | Removed; startup warm-up only | −3–10s |
| Conversation history | Unlimited turns | Truncated to last 10 turns | −1–3s |
| Retry delays | 1s → 2s → 4s | 0.5s → 1s | −3–7s on failure |

### Key Methods

| Method | Purpose |
|--------|---------|
| `_get_shared_client(base_url)` | Returns or creates singleton `httpx.AsyncClient` with keep-alive |
| `generate_content_async()` | Main generation method. Builds Ollama payload, calls API, truncates response at sentence boundary |
| `warm_up_model()` | Sends 1-token request at startup to pre-load model into GPU VRAM |
| `_extract_text_from_contents()` | Delegates to `llm_utils.extract_text_from_contents()` — shared with GeminiLlm |

### Ollama Request Payload

```json
{
  "model": "gemma3:4b",
  "prompt": "<system>...</system>\n<turn>...</turn>",
  "stream": false,
  "options": {
    "num_ctx": 2048,
    "num_predict": 400,
    "temperature": 0.7
  }
}
```

---

## GeminiLlm (`backend/llms/gemini_llm.py`)

### What It Does

Extends `google.adk.models.BaseLlm`. Uses the `google.genai` SDK with **streaming enabled** to reduce first-token latency.

### Configuration (set in `__init__`)

```python
max_output_tokens: int = 800   # optimised from 2048
timeout: float = 45.0          # reduced from 60s
max_retries: int = 2           # reduced from 3
temperature: float = 0.7
top_p: float = 0.95
top_k: int = 40
```

### Key Methods

| Method | Purpose |
|--------|---------|
| `_generate_with_stream(prompt)` | Calls `generate_content_stream()`, collects all chunks, joins to final text |
| `_retry_with_backoff(func)` | Exponential backoff retry for 429 / 503 / timeout errors |
| `_get_generation_config()` | Returns `GenerateContentConfig` with all params |
| `_get_safety_settings()` | Disables all safety filters (required for scam simulation content) |

### Safety Settings

All safety categories are set to `BLOCK_NONE`. This is intentional — the platform simulates scam conversations which would otherwise be blocked by default Gemini safety filters.

### Client Singleton

`genai.Client` is created once in `__init__` and reused across all calls (stored as `_client` PrivateAttr). API key is read from `GEMINI_API_KEY` env var.

---

## Shared Utility: `llm_utils.py`

`backend/llms/llm_utils.py` provides `extract_text_from_contents(contents)` — previously duplicated in both `ollama_llm.py` and `gemini_llm.py` (DUP-001 fix). Both adapters now import from here.

```python
# Both adapters use:
from llms.llm_utils import extract_text_from_contents
```

Converts ADK `Content` list (with `role` + `parts`) into a flat prompt string, truncated to the last 10 conversation turns.

---

## LlmFactory (`backend/llms/llm_factory.py`)

Static factory class. Single entry point for all agent LLM creation.

### Key Methods

| Method | Signature | Purpose |
|--------|-----------|---------|
| `create_llm` | `(agent_type, scam_type, context, use_gemini)` | Creates and returns OllamaLlm or GeminiLlm with injected RAG context |
| `get_rag_context` | `(scam_type, context)` | Queries ChromaDB, returns formatted context string |
| `get_current_provider` | `()` | Returns `'gemini'` or `'ollama'` |
| `get_provider_info` | `()` | Returns full config dict (model names, URLs, token limits) |
| `validate_gemini_config` | `()` | Checks `GEMINI_API_KEY` is set and model IDs are valid |

### Per-Agent Model Overrides

Different models can be assigned per agent type via env vars:

```bash
# Gemini per-agent overrides
GEMINI_MODEL_SCAMMER=gemini-2.0-flash-exp
GEMINI_MODEL_EXPERT=gemini-2.0-flash-exp

# Ollama per-agent overrides (after Tools Center fine-tune)
AGENT_MODEL_SCAMMER=scammer-sim
AGENT_MODEL_EXPERT=anti-fraud-expert
AGENT_MODEL=gemma3:4b          # default for all others
```

---

## Runtime Provider Switching

`POST /api/model/switch` (`model_switch_routes.py`) updates the `GEMINI_ENABLED` flag at runtime. No restart required. The change is reflected immediately in the next `LlmFactory.create_llm()` call.

See [model-switch-api.md](model-switch-api.md) for full API reference.

---

## Relevant Files

```
backend/llms/
  ollama_llm.py         Ollama adapter
  gemini_llm.py         Gemini adapter
  llm_factory.py        Provider selection + RAG injection
  llm_utils.py          Shared extract_text_from_contents()
  rag_integration.py    GeminiRAGHelper singleton
  rag_diagnostics.py    RAG health check
  gemini_file_manager.py  Gemini file upload (unused in current HK deployment)
backend/.env            GEMINI_ENABLED, API keys, model names
```

---

## Related Features

- [model-switch-api.md](model-switch-api.md) — Runtime provider switching
- [rag-knowledge-base.md](rag-knowledge-base.md) — RAG context injected by LlmFactory
- [parallel-generation.md](parallel-generation.md) — asyncio.gather over both LLMs
- [tools-center.md](tools-center.md) — Creates custom Ollama models for per-agent overrides
