# Feature: RAG Knowledge Base

> Category: Secondary | Version: 4.1 | Last Updated: 2026-03-11

---

## Overview

The RAG (Retrieval-Augmented Generation) system retrieves **real Hong Kong scam cases** from a ChromaDB vector store and injects them into agent prompts at request time. This grounds every AI response in documented, real-world fraud patterns rather than generic LLM knowledge.

---

## Data Source

- **281 real HK scam cases** documented by ADCC (Anti-Deception Coordination Centre)
- Scraped from the ADCC website via `backend/scripts/scraper.py`
- Raw data stored in `data/scraped_alerts.json`
- Embedded and indexed into ChromaDB at `backend/db/chroma_db/`
- JSON backup at `backend/agents/scam_knowledge_base.json`

---

## Architecture

```
Request arrives at rpgv2_game_modes_routes.py
  │
  ▼
LlmFactory.create_llm(agent_type, scam_type='investment')
  │
  ▼
LlmFactory.get_rag_context(scam_type)
  │
  ▼
GeminiRAGHelper.query(scam_type)          ← singleton instance
  │
  ▼
rag_service.query_db(collection, query, n_results=3)
  │   ChromaDB semantic search
  ▼
Top-N relevant case snippets returned
  │
  ▼
Appended to agent system_instruction
  │
  ▼
LLM call made with enriched prompt
```

---

## ChromaDB Configuration

From `backend/config.py` → `DatabaseConfig`:

```python
CHROMA_PATH = 'backend/db/chroma_db'
CHROMA_COLLECTION_NAME = 'scam_cases'
RAG_DEFAULT_RESULTS = 3
RAG_MAX_RESULTS = 10
```

The ChromaDB store is **persistent** — it survives server restarts. It is excluded from deployment packages (see `docs/exclude_list.txt`) because each deployment generates its own embeddings.

---

## GeminiRAGHelper Singleton

File: `backend/llms/rag_integration.py`

- Created once and reused across all requests (singleton pattern)
- Holds a reference to the ChromaDB client and collection
- `query(scam_type, context)` → returns a formatted string ready for prompt injection
- Falls back gracefully if ChromaDB is unavailable (logs warning, returns empty string)

---

## Prompt Injection Format

The retrieved cases are appended to the system instruction in this format:

```
## 相關真實香港詐騙案例

案例1: [Case title]
手法: [Tactic description]
結果: [Outcome]

案例2: ...
```

This injection happens **per request** — each LLM call gets fresh, scam-type-relevant context.

---

## Scam Type Mapping

The `scam_type` parameter from the frontend maps to ChromaDB query terms:

| Frontend scam_type | ChromaDB query |
|-------------------|----------------|
| `investment` | 投資詐騙, 保證回報 |
| `phishing` | 網絡釣魚, 假冒銀行 |
| `romance` | 網上情緣, 假扮伴侶 |
| `impersonation` | 假冒官員, 警察來電 |
| `online_shopping` | 網購詐騙, 先付款 |

---

## RAG Diagnostics

File: `backend/llms/rag_diagnostics.py`

Provides health check functions:
- `check_chroma_connection()` — verifies ChromaDB is accessible
- `get_collection_stats()` — returns document count and collection metadata
- `run_test_query(scam_type)` — runs a sample query and returns results

Called at startup if `RAG_DIAGNOSTICS=true` in `.env`.

---

## Relevant Files

```
backend/llms/rag_integration.py       GeminiRAGHelper singleton + prompt formatting
backend/services/rag_service.py       Low-level query_db() ChromaDB interface
backend/llms/rag_diagnostics.py       Health checks and diagnostics
backend/db/chroma_db/                 Persistent vector store (gitignored)
backend/agents/scam_knowledge_base.json  281 cases JSON backup
data/scraped_alerts.json              Raw ADCC scraped data
backend/scripts/scraper.py            ADCC scraper (feeds this pipeline)
```

---

## Related Features

- [llm-backend.md](llm-backend.md) — LlmFactory calls RAG before creating LLM
- [tools-center.md](tools-center.md) — Scraper tool that refreshes source data
- [multi-agent-system.md](multi-agent-system.md) — Which agents receive RAG injection
