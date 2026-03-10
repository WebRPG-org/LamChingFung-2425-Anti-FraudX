# AI Anti-Fraud Platform v4

> A full-stack educational platform simulating real-world Hong Kong fraud scenarios using a Multi-Agent AI system. Players interact through a 2D RPG game, facing AI-driven scammers while guided by an AI expert — powered by local Ollama or Google Gemini API.

---

## Features

- **4 AI Agents** — Scammer, Expert, Victim, Recorder operating simultaneously
- **281 real HK scam cases** — RAG-injected from ADCC knowledge base (ChromaDB)
- **Dual LLM backend** — Local Ollama (privacy-first) or Google Gemini API (cloud)
- **RPGv2 Battle Scene** — Phaser.js 2D world map with HTML overlay battle UI
- **Real-time trust meter** — 3-dimension trust tracking drives win/loss outcome
- **Parallel AI generation** — `asyncio.gather()` cuts response time ~50%
- **Tools Center** — Web dashboard for scraping, fine-tuning, and Ollama model creation
- **Docker support** — Local, GCP, and AWS deployment configs included
- **Ansible automation** — One-command deployment to any Linux server

---

## Quick Start

### Option A — Local with Ollama (Privacy-first)

**Requirements**: Python 3.10+, [Ollama](https://ollama.ai) installed

```bash
# 1. Clone
git clone <repo-url>
cd AI-Agentv4

# 2. Install Ollama model
ollama pull gemma3:4b

# 3. Install backend dependencies
cd backend
pip install -r requirements.txt

# 4. Configure (Ollama mode)
cp env.example backend/.env
# Edit backend/.env: set GEMINI_ENABLED=false

# 5. Start
quick_start.bat          # Windows
python backend/main.py   # Manual
```

### Option B — Cloud with Gemini API

```bash
# 1-3. Same as above

# 4. Configure (Gemini mode)
cp env.example backend/.env
# Edit backend/.env:
#   GEMINI_ENABLED=true
#   GEMINI_API_KEY=your_key_here

# 5. Start
quick_start_gemini.bat   # Windows
python backend/main.py   # Manual
```

### Option C — Docker

```bash
# Local GPU + Ollama
docker compose up --build

# Host Ollama or Gemini (no GPU needed)
docker compose -f docker-compose.local.yml up --build

# Gemini only
GEMINI_ENABLED=true GEMINI_API_KEY=xxx \
  docker compose -f docker-compose.local.yml up --build
```

**Access the platform:**

| URL | Purpose |
|-----|---------|
| http://localhost:8000/rpgv2 | RPGv2 Game (primary) |
| http://localhost:8000/ | Dashboard |
| http://localhost:8000/tools | Tools Center |
| http://localhost:8000/docs | API docs (Swagger) |
| http://localhost:8000/health | Health check |

---

## System Requirements

| Mode | CPU | RAM | GPU | Notes |
|------|-----|-----|-----|-------|
| Ollama (gemma3:4b) | 4 cores | 8 GB | Optional | GPU recommended |
| Gemini API | 2 cores | 4 GB | None | Requires API key |
| Docker (local) | 4 cores | 8 GB | Optional | NVIDIA Container Toolkit for GPU |

---

## Project Structure

```
AI-Agentv4/
├── backend/                    FastAPI backend (port 8000)
│   ├── agents/                 ScammerAgent, ExpertAgent, VictimAgent, RecorderAgent
│   ├── api/                    15 FastAPI route files
│   ├── llms/                   OllamaLlm, GeminiLlm, LlmFactory, RAG
│   ├── models/                 Modelfile.expert, Modelfile.scammer
│   ├── scripts/                25 utility scripts (scraper, finetune, etc.)
│   ├── services/               AgentService, SimulationRunner, RAGService
│   ├── utils/                  29 utility modules
│   ├── db/chroma_db/           ChromaDB vector store (281 HK scam cases)
│   ├── config.py               Centralized config (9 sections)
│   ├── main.py                 App entry point (15 routers)
│   └── requirements.txt
├── rpg-platform-v2/            Phaser.js + TypeScript RPG game (port 3000)
│   └── src/scenes/             BattleScene, WorldMapScene, AutoModeScene, ResultScene
├── frontend/                   Plain HTML/JS dashboard (9 pages)
│   └── tools.html              Tools Center UI
├── data/                       Scraped ADCC data
├── docs/
│   ├── ARCHITECTURE.md         System architecture
│   ├── CORE_FEATURES.md        Core feature documentation
│   ├── SECONDARY_FEATURES.md   Secondary feature documentation
│   ├── DOCKER_DEPLOY.md        Docker deployment guide
│   └── features/               19 individual feature documents
├── docker/                     Docker build files
├── ansible/                    Ansible deployment automation
├── docker-compose.yml          Local GPU + Ollama
├── docker-compose.local.yml    Host Ollama or Gemini
├── docker-compose.gcp.yml      GCP (Cloud Run / GCE GPU)
├── docker-compose.aws.yml      AWS (App Runner / EC2 GPU)
├── quick_start.bat             Windows startup (Ollama)
├── quick_start_gemini.bat      Windows startup (Gemini)
└── env.example                 Environment variable template
```

---

## Configuration

All configuration lives in `backend/.env`. Copy `env.example` to start:

```bash
cp env.example backend/.env
```

**Key variables:**

```bash
# LLM Provider
GEMINI_ENABLED=false          # true = Gemini API, false = Ollama
GEMINI_API_KEY=your_key_here

# Ollama
AGENT_MODEL=gemma3:4b
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_NUM_CTX=2048           # Optimised from 4096
OLLAMA_NUM_PREDICT=400        # Optimised from 2000

# Per-agent model overrides (optional, after Tools Center)
AGENT_MODEL_SCAMMER=scammer-sim
AGENT_MODEL_EXPERT=anti-fraud-expert

# Gemini per-agent models
GEMINI_MODEL_SCAMMER=gemini-2.5-flash
GEMINI_MODEL_EXPERT=gemini-2.5-flash
GEMINI_MAX_OUTPUT_TOKENS=800

# App
APP_ENV=development
LOG_LEVEL=info
FORCE_GPU=0
```

> **Important**: Do NOT wrap values in quotes in `.env`.
> Use `GEMINI_ENABLED=true`, NOT `GEMINI_ENABLED='true'`.

---

## Deployment

### Docker (Recommended)

See [`docs/DOCKER_DEPLOY.md`](docs/DOCKER_DEPLOY.md) for full instructions.

```bash
# GCP Cloud Run (Gemini)
docker compose -f docker-compose.gcp.yml up

# AWS ECS (Gemini)
docker compose -f docker-compose.aws.yml up

# GCE / EC2 with GPU + Ollama
docker compose -f docker-compose.gcp.yml --profile ollama up
```

### Ansible (Bare Metal / VM)

See [`ansible/README.md`](ansible/README.md) for full instructions.

```bash
# Configure inventory
cp ansible/inventory/hosts.example.yml ansible/inventory/hosts.yml
# Edit hosts.yml with your server IPs

# Deploy (Ollama mode)
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/site.yml

# Deploy (Gemini mode)
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/site.yml \
  -e "gemini_enabled=true gemini_api_key=your_key"

# GCP / AWS
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/deploy-gcp.yml
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/deploy-aws.yml
```

---

## Tools Center

A web-based pipeline for training custom Ollama models — accessible at `/tools`.

| Step | Action | Output |
|------|--------|--------|
| 1 | Scrape ADCC data | `data/scraped_alerts.json` |
| 2 | Generate fine-tune data | `backend/training_data/fine_tuning_data/*.jsonl` |
| 3 | Generate Modelfiles | `backend/models/Modelfile.expert` + `Modelfile.scammer` |
| 4 | Create Ollama models | `anti-fraud-expert`, `scammer-sim` in Ollama |

After step 4, set in `backend/.env`:
```bash
AGENT_MODEL_EXPERT=anti-fraud-expert
AGENT_MODEL_SCAMMER=scammer-sim
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Full system architecture |
| [`docs/CORE_FEATURES.md`](docs/CORE_FEATURES.md) | Core feature reference |
| [`docs/SECONDARY_FEATURES.md`](docs/SECONDARY_FEATURES.md) | Secondary feature reference |
| [`docs/DOCKER_DEPLOY.md`](docs/DOCKER_DEPLOY.md) | Docker deployment guide |
| [`docs/features/INDEX.md`](docs/features/INDEX.md) | All 18 feature documents |
| [`ansible/README.md`](ansible/README.md) | Ansible deployment guide |

---

## Troubleshooting

**Gemini API quota exceeded (`429 RESOURCE_EXHAUSTED`)**
```
Free tier: limited requests/day. Wait for reset or upgrade billing account.
Alternative: switch to Ollama (GEMINI_ENABLED=false).
```

**Ollama not responding**
```bash
ollama serve          # Start Ollama
ollama list           # Check models installed
ollama pull gemma3:4b # Pull model if missing
```

**`GEMINI_ENABLED` not switching to Gemini**
```
Check backend/.env — value must NOT have quotes:
  Correct:   GEMINI_ENABLED=true
  Wrong:     GEMINI_ENABLED='true'
```

**ChromaDB / RAG errors**
```bash
pip install --upgrade chromadb sentence-transformers
# ChromaDB is auto-created at backend/db/chroma_db/ on first run
```

**Docker: host Ollama not reachable**
```bash
# Windows/Mac: http://host.docker.internal:11434 (works automatically)
# Linux: add to docker-compose.local.yml extra_hosts (already included)
```

---

## License

For educational and research purposes.
