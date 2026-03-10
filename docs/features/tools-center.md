# Feature: Tools Center

> Category: Secondary | Version: 4.1 | Last Updated: 2026-03-11

---

## Overview

A **web-based model training pipeline dashboard** (`frontend/tools.html`) that lets developers run the full pipeline — from scraping live ADCC scam data to creating custom fine-tuned Ollama models — entirely through a browser UI, with real-time log streaming.

---

## Pipeline Overview

```
Step 1: Scrape ADCC website
    scraper.py → data/scraped_alerts.json
         │
Step 2: Generate fine-tune training data
    generate_finetuning_data.py → backend/training_data/fine_tuning_data/*.jsonl
         │
Step 3: Generate Ollama Modelfiles
    model_fine_tuning.py → backend/models/Modelfile.expert
                         → backend/models/Modelfile.scammer
         │
Step 4: Create Ollama models
    ollama create anti-fraud-expert -f Modelfile.expert
    ollama create scammer-sim -f Modelfile.scammer
         │
Step 5: Activate in backend/.env
    AGENT_MODEL_EXPERT=anti-fraud-expert
    AGENT_MODEL_SCAMMER=scammer-sim
```

---

## Backend Architecture

File: `backend/api/tools_routes.py`

### ProcState

Each pipeline step runs as a managed subprocess:

```python
class ProcState:
    proc: subprocess.Popen      # The running process
    log_lines: list             # Captured stdout lines
    exit_code: Optional[int]    # None while running
    lock: threading.Lock

    def start(cmd, cwd, env) -> (bool, pid_or_error)
    def status() -> { running, exit_code, log[] }
```

Three independent instances: `_scraper`, `_finetune`, `_modelgen`

Each runs in a background thread that drains stdout line-by-line into `log_lines`. The frontend polls `/status` every 2 seconds to show live output.

---

## API Endpoints

### Scraper

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/tools/scraper/run` | Start `scripts/scraper.py` |
| GET | `/api/tools/scraper/status` | `{ running, exit_code, log[], data_count }` |

### Fine-tune Data Generation

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/tools/finetune/run` | Start `scripts/generate_finetuning_data.py` |
| GET | `/api/tools/finetune/status` | `{ running, exit_code, log[], ft_file_count }` |
| GET | `/api/tools/finetune/files` | List generated JSONL files with sizes |

### Modelfile Generation + Ollama Create

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/tools/modelgen/run` | Start `scripts/model_fine_tuning.py` |
| GET | `/api/tools/modelgen/status` | `{ running, exit_code, log[], model_files[] }` |
| POST | `/api/tools/modelgen/ollama-create-both` | Run `ollama create` for expert + scammer sequentially |
| POST | `/api/tools/modelgen/ollama-create` | Run `ollama create` for a single model |
| GET | `/api/tools/modelgen/ollama-list` | List installed Ollama models |

---

## Scripts

### `backend/scripts/scraper.py`
- Uses Selenium to scrape ADCC alert pages
- Outputs structured JSON to `data/scraped_alerts.json`
- Run time: 2–10 minutes depending on ADCC site load

### `backend/scripts/generate_finetuning_data.py`
- Reads `data/scraped_alerts.json`
- Converts cases into JSONL conversation format for Ollama fine-tuning
- Outputs to `backend/training_data/fine_tuning_data/`

### `backend/scripts/model_fine_tuning.py`
- Reads fine-tuning JSONL files
- Generates `backend/models/Modelfile.expert` and `backend/models/Modelfile.scammer`
- Each Modelfile embeds the base model + SYSTEM prompt + training examples

---

## Activating Custom Models

After `ollama create` completes, set in `backend/.env`:

```bash
AGENT_MODEL_EXPERT=anti-fraud-expert
AGENT_MODEL_SCAMMER=scammer-sim
```

`LlmFactory` picks up these overrides on the next `create_llm()` call. No restart needed if Model Switch API is used.

---

## Relevant Files

```
backend/api/tools_routes.py                  All /api/tools/* endpoints + ProcState
backend/scripts/scraper.py                   ADCC scraper
backend/scripts/generate_finetuning_data.py  JSONL generator
backend/scripts/model_fine_tuning.py         Modelfile generator
backend/models/Modelfile.expert              Generated expert model definition
backend/models/Modelfile.scammer             Generated scammer model definition
backend/training_data/fine_tuning_data/      JSONL output directory
data/scraped_alerts.json                     Scraped ADCC data
frontend/tools.html                          UI dashboard
```

---

## Related Features

- [rag-knowledge-base.md](rag-knowledge-base.md) — Scraped data also feeds ChromaDB
- [llm-backend.md](llm-backend.md) — Custom models used via per-agent overrides
- [model-switch-api.md](model-switch-api.md) — Switch to custom models at runtime
