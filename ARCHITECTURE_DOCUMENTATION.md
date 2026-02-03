# AI Anti-Fraud Training Platform - Architecture Documentation

## 📋 Executive Summary

This is a **multi-agent AI simulation platform** designed for anti-fraud education in Hong Kong. It uses **Google ADK (Agent Development Kit)** with **Ollama** local LLMs to simulate realistic scam scenarios through conversations between AI agents (Scammer, Victim, Expert, Recorder).

**Key Technologies:**
- **Backend**: FastAPI + Python 3.10+
- **AI Framework**: Google ADK (Agent Development Kit)
- **LLM**: Ollama (Gemma3 4B/27B, Mistral 7B) - Local deployment
- **Database**: SQLite3 + ChromaDB (Vector DB for RAG)
- **Frontend**: HTML/CSS/JavaScript + RPG Maker MV integration
- **Deployment**: Docker + Docker Compose (GPU support)
- **Code Quality**: Custom exceptions, centralized config, 100+ unit tests ✨ **NEW**

---

## 🏗️ System Architecture

### 1. Multi-Layer Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Client Layer                              │
│  - Web UI (HTML/JS)                                          │
│  - RPG Maker Game (with custom plugins)                     │
│  - Personal Chat Interface                                   │
└─────────────────────────────────────────────────────────────┘
                            ↓ HTTP/WebSocket
┌─────────────────────────────────────────────────────────────┐
│                    API Layer (FastAPI)                       │
│  - game_routes_v2.py (RPG integration)                       │
│  - simulation_routes.py (Auto simulation)                    │
│  - personal_chat_routes.py (1-on-1 chat)                     │
│  - training_routes.py (Data access)                          │
│  - websocket_manager.py (Real-time events)                   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                Service Layer (Core Logic)                    │
│  - AgentService: Unified agent management                    │
│  - SimulationRunner: Multi-round orchestration              │
│  - RAGService: Knowledge retrieval                           │
│  - VisionService: Image analysis (future)                    │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│              AI Agent Layer (Google ADK)                     │
│  - VictimAgent (3 personas: elderly/average/overconfident)   │
│  - ScammerAgent (10+ scam tactics)                           │
│  - ExpertAgent (Anti-fraud advisor)                          │
│  - RecorderAgent (Analysis & scoring)                        │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│              LLM Infrastructure Layer                        │
│  - OllamaLlm: Wrapper for Ollama API                         │
│  - Ollama Service: Local LLM server (Gemma3/Mistral)         │
│  - GPU Acceleration: NVIDIA CUDA support                     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  Data Storage Layer                          │
│  - SQLite3: Session history, conversations                   │
│  - ChromaDB: Vector knowledge base (RAG)                     │
│  - JSON Files: Training data, configs                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 🤖 Core Components

### 1. AI Agents (Google ADK)

#### **VictimAgent** (`backend/agents/victim.py`)
- **Purpose**: Simulates potential fraud victims with different vulnerability levels
- **Personas**:
  - `elderly`: 72-year-old retired cleaner, trusts authority, fears technology
  - `average`: 35-year-old office worker, cautious but can be persuaded
  - `overconfident`: 28-year-old IT engineer, overconfident, may leak info
  - `student`: 21-year-old university student, curious but inexperienced
- **Trust System**: Dynamic trust scores (0-100) for scammer and expert
- **Key Features**:
  - Emotional state tracking (calm/anxious/panicked/suspicious)
  - Gradual trust changes (max ±12-15 per turn based on persona)
  - Role consistency enforcement (prevents acting like expert)

#### **ScammerAgent** (`backend/agents/scammer.py`)
- **Purpose**: Simulates professional scammers using real-world tactics
- **Scam Tactics** (10+ types):
  - Fake official/bank impersonation
  - Investment scams (crypto, stocks)
  - Phishing (SMS, email, WhatsApp)
  - Romance scams
  - Prize/lottery scams
  - Job scams (fake recruitment)
- **Key Features**:
  - Authority manipulation (impersonates police, banks, government)
  - Urgency creation ("immediate action required")
  - Emotional exploitation (fear, greed, FOMO)
  - Counter-expert strategies (discredits expert advice)
  - RAG tool: Queries real scam cases for realistic tactics

#### **ExpertAgent** (`backend/agents/expert.py`)
- **Purpose**: Anti-fraud advisor (retired police officer "黃sir")
- **Key Features**:
  - Evidence-based warnings (uses RAG to cite real cases)
  - Empathy + actionable advice (安撫情緒 + 具體步驟)
  - Structured response format (emoji sections: 🚨📋⚠️✅)
  - Image analysis support (analyzes phishing screenshots)
  - Hotline provision (18222, 999, etc.)
- **Response Template**:
  ```
  🚨 **[One-line judgment]**
  📋 **Why it's a scam**: • Point 1 • Point 2 • Point 3
  ⚠️ **Scammer's next move**: "[Prediction]" - Don't believe!
  ✅ **What to do now**: • Action 1 • Action 2 • Action 3
  ```

#### **RecorderAgent** (`backend/agents/recorder.py`)
- **Purpose**: Analyzes conversations and generates performance reports
- **Output**: JSON report with scores for scammer and expert (0-100)

---

### 2. Service Layer

#### **AgentService** (`backend/services/agent_service.py`)
- **Purpose**: Unified interface for all agent operations
- **Key Methods**:
  - `generate_response()`: Generates AI response with optional tracking
  - `generate_final_analysis()`: Uses RecorderAgent for end-of-game report
  - `get_current_trust()`: Returns victim's trust scores
- **Features**:
  - Role consistency checking (via RoleEnforcer)
  - Performance tracking (via PerformanceTracker)
  - Context management (conversation history)
  - Image support (base64 encoded images for vision analysis)

#### **SimulationRunner** (`backend/services/simulation_runner.py`)
- **Purpose**: Orchestrates multi-round conversations
- **Flow**:
  1. Scammer speaks → Victim responds
  2. Expert intervenes → Victim responds
  3. Repeat for 10-15 rounds or until outcome
- **Outcome Detection**:
  - **Scammer wins**: Victim trust in scammer ≥ 80
  - **Expert wins**: Victim trust in expert ≥ 75 AND trust in scammer < 40
  - **Victim alert**: Alertness ≥ 80
- **Auto-training**: Automatically starts new rounds with random personas/tactics

---

### 3. Utility Systems

#### **PerformanceTracker** (`backend/utils/performance_tracker.py`)
- **Purpose**: Real-time tracking of trust dynamics and agent performance
- **Trust Mechanics**:
  - **Inertia multiplier**: Harder to change trust when already high/low
  - **Fatigue multiplier**: Repeated tactics lose effectiveness
  - **Emotional multiplier**: Emotional state affects persuasion
  - **Persona multiplier**: Different personas react differently to tactics
  - **Combination bonus**: Multiple tactics together are more effective
- **Scoring**:
  - Scammer: Persuasiveness, credibility, pressure effectiveness
  - Expert: Intervention effectiveness, clarity, empathy, actionability

#### **RoleEnforcer** (`backend/utils/role_enforcer.py`)
- **Purpose**: Prevents role collapse and maintains character consistency
- **Checks**:
  - **Scammer**: Cannot express fear, ask for help, or reveal identity
  - **Victim**: Cannot comfort others or act like expert
  - **Expert**: Cannot request sensitive data or impersonate officials
- **Detection**:
  - Forbidden phrases (e.g., scammer saying "我好驚")
  - Role confusion (scammer saying victim's lines)
  - Repetition loops (same response multiple times)
  - Meta-language (script examples, teaching content)

---

## 🎮 User Interfaces

### 1. Web UI (`frontend/index.html`)
- **Modes**:
  - **RPG Game Mode**: Interactive game with NPC dialogues
  - **Auto Simulation Mode**: Watch AI agents converse (3-way dialogue)
  - **Personal Chat Mode**: 1-on-1 chat with expert or scammer
  - **API Test Mode**: Developer testing interface

### 2. RPG Maker Integration (`rpg_maker_plugins/`)
- **Plugins**:
  - `SimulationTraining.js`: Main plugin for AI dialogue in RPG
  - `AI_Bridge.js`: API communication bridge
  - `AntiFraudGame.js`: Game mechanics integration
- **Features**:
  - NPC-triggered AI conversations
  - Persona and scam tactic rotation
  - Real-time dialogue display in game

---

## 🗄️ Data Storage

### 1. SQLite3 (`anti_fraud_game.db`)
- **Tables**:
  - `sessions`: Game sessions with persona type
  - `conversations`: Message history (role, message, timestamp)
  - `training_data`: Collected dialogue data for fine-tuning

### 2. ChromaDB (`backend/db/chroma_db/`)
- **Purpose**: Vector database for RAG (Retrieval-Augmented Generation)
- **Content**: Real scam cases from Hong Kong Police and Consumer Council
- **Usage**: Agents query similar cases to provide evidence-based responses

### 3. JSON Files
- `training_data/`: Conversation logs for model fine-tuning
- `arms_race_data/`: Evolution data for scammer/expert improvement
- `agent_versions/`: Historical agent versions

---

## 🛡️ Code Quality Infrastructure ✨ **NEW**

### 1. Exception Handling (`backend/exceptions.py`)

**Custom Exception Hierarchy**:
```python
AntiFraudException (base)
├── AgentException
│   ├── AgentInitializationError
│   ├── AgentResponseError
│   ├── RoleConsistencyError
│   └── PersonaNotFoundError
├── LLMException
│   ├── OllamaConnectionError
│   ├── ModelNotFoundError
│   ├── LLMTimeoutError
│   └── LLMResponseTooLongError
├── DatabaseException
│   ├── SessionNotFoundError
│   └── DatabaseConnectionError
├── ValidationException
│   ├── InputTooLongError
│   └── InvalidScamTacticError
├── SimulationException
│   ├── SimulationNotFoundError
│   ├── SimulationAlreadyStoppedError
│   └── MaxRoundsExceededError
├── RAGException
│   ├── VectorDBConnectionError
│   └── NoRAGResultsError
└── RateLimitException
    └── RateLimitExceededError
```

**Benefits**:
- Specific error types for better debugging
- Rich error context (details dict)
- Easier error handling in API routes
- Better error messages for users

**Example**:
```python
try:
    tracker = PerformanceTracker(persona_type="invalid")
except PersonaNotFoundError as e:
    print(f"Error: {e.message}")
    print(f"Available: {e.available_personas}")
```

---

### 2. Configuration Management (`backend/config.py`)

**Centralized Configuration Modules**:

1. **TrustConfig**: Trust thresholds, change limits, multipliers
   - `SCAMMER_WIN_THRESHOLD = 80`
   - `EXPERT_WIN_THRESHOLD = 75`
   - `MAX_TRUST_CHANGE_ELDERLY = 12`
   - Inertia multipliers (0.5-1.0)
   - Fatigue multipliers (0.5-1.0)
   - Emotional multipliers (0.5-1.5)

2. **SimulationConfig**: Round limits, timing, auto-training
   - `MAX_ROUNDS = 15`
   - `FAST_MODE_DELAY = 0.5`
   - `AUTO_TRAIN_ENABLED = true`

3. **LLMConfig**: Model names, URLs, generation parameters
   - Model names per agent
   - Ollama URLs per agent
   - Temperature, top_p, repeat_penalty
   - Timeout and retry configuration

4. **ValidationConfig**: Input limits, rate limiting
   - `MAX_MESSAGE_LENGTH = 1000`
   - `RATE_LIMIT_REQUESTS = 10`
   - `RATE_LIMIT_WINDOW_SECONDS = 60`

5. **DatabaseConfig**: Paths, timeouts, RAG settings
6. **PersonaConfig**: Available personas, display names
7. **ScamTacticsConfig**: Available tactics, categories
8. **LoggingConfig**: Log levels, formats, file paths

**Usage**:
```python
from config import config

# Access constants
if trust >= config.trust.SCAMMER_WIN_THRESHOLD:
    return "scammer_wins"

# Get persona-specific values
max_change = config.get_max_trust_change("elderly")
initial_trust = config.get_initial_trust("elderly")

# Validate inputs
if config.validate_persona(persona_type):
    print("Valid persona")
```

**Benefits**:
- No magic numbers in code
- Easy to tune parameters
- Environment variable support
- Type safety with dataclasses
- Single source of truth

---

### 3. Input Validation (`backend/utils/validation.py`)

**Pydantic Models with Validation**:

```python
class ValidatedMessageRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="User message"
    )
    
    @field_validator('message')
    @classmethod
    def validate_message_content(cls, v: str) -> str:
        # Check for prompt injection
        dangerous_patterns = [
            r"ignore\s+previous\s+instructions",
            r"system\s*:",
        ]
        for pattern in dangerous_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError("Dangerous content detected")
        return v.strip()
```

**Validation Features**:
- ✅ Length limits (1-1000 characters)
- ✅ Prompt injection detection
- ✅ Persona validation
- ✅ Scam tactic validation
- ✅ Image validation (size, count)
- ✅ Session ID format validation

**Rate Limiting**:
```python
rate_limiter = RateLimiter()
if not rate_limiter.check_rate_limit(client_ip):
    raise RateLimitExceededError(10, 60, retry_after)
```

**Benefits**:
- Prevents DoS attacks
- Blocks prompt injection
- Better error messages
- Type-safe requests

---

### 4. Test Suite (`backend/tests/`)

**Test Coverage**: 100+ unit tests

**Test Files**:
1. **`test_performance_tracker.py`** (40+ tests)
   - Initialization tests
   - Trust inertia calculations
   - Strategy fatigue detection
   - Emotional multipliers
   - Scammer/Expert analysis
   - Outcome detection
   - Integration scenarios

2. **`test_role_enforcer.py`** (50+ tests)
   - Scammer consistency checks
   - Expert consistency checks
   - Victim consistency checks
   - Repetition detection
   - Dialogue flow analysis
   - Edge cases

3. **`conftest.py`** - Shared fixtures
4. **`pytest.ini`** - Test configuration

**Running Tests**:
```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html

# Run specific test
pytest tests/test_performance_tracker.py::TestTrustInertia -v
```

**Benefits**:
- Confidence in refactoring
- Regression prevention
- Documentation through tests
- Faster debugging

---

## 🐳 Docker Deployment

### Configuration Files
- `docker-compose.yml`: Base config (Ollama + Backend)
- `docker-compose.local.yml`: Uses host's Ollama (Windows recommended)
- `docker-compose.dev.yml`: Development mode (hot reload)
- `docker-compose.prod.yml`: Production mode (multi-worker, resource limits)

### Services
1. **ollama**: Ollama LLM service (GPU-accelerated)
2. **ai-antiscam-backend**: FastAPI application

### GPU Support
- **Runtime**: NVIDIA Docker Runtime
- **Environment**: `OLLAMA_LLM_LIBRARY=cuda`, `NVIDIA_VISIBLE_DEVICES=all`
- **Health Check**: Ensures Ollama is ready before backend starts

---

## 🔄 Key Workflows

### Workflow 1: Auto Simulation
```
1. User clicks "Start Simulation" on Web UI
2. POST /simulation/start → Creates simulation_id
3. WebSocket connection established
4. SimulationRunner orchestrates:
   - Round 1: Scammer → Victim → Expert → Victim
   - Round 2-15: Repeat with trust updates
5. Outcome detected → RecorderAgent generates report
6. If auto_train=true → Start new round with random settings
```

### Workflow 2: RPG Game Mode
```
1. Player talks to NPC in RPG Maker game
2. Plugin sends POST /api/game/v2/message
3. AgentService generates AI response (scammer or expert)
4. Response sent back to game → Displayed in dialogue box
5. Trust scores updated → Affects game outcome
```

### Workflow 3: Personal Chat
```
1. User selects mode (expert or scammer) and scam type
2. POST /api/personal-chat/start → Creates session
3. User sends message → POST /api/personal-chat/message
4. AgentService generates response
5. Conversation continues until user ends session
```

---

## 🧠 Advanced Features

### 1. RAG (Retrieval-Augmented Generation)
- **Purpose**: Provide evidence-based responses using real scam cases
- **Implementation**: ChromaDB vector search
- **Usage**:
  - ExpertAgent: Cites real cases to warn victims
  - ScammerAgent: Learns realistic tactics from past cases

### 2. Dynamic Trust System
- **Victim Trust Scores**: 0-100 for scammer and expert
- **Factors**:
  - Agent tactics (authority, urgency, empathy)
  - Persona type (elderly more trusting)
  - Emotional state (anxious → more vulnerable)
  - Strategy fatigue (repeated tactics lose effect)
  - Psychological inertia (hard to change high trust)

### 3. Role Consistency Enforcement
- **Problem**: LLMs may "role collapse" (scammer acts like victim)
- **Solution**: RoleEnforcer checks every response
- **Actions**: Logs warnings, can trigger rewrite (future feature)

### 4. Multi-Instance Ollama (Optional)
- **Purpose**: Maximize GPU utilization
- **Setup**: Run 4 Ollama instances on different ports
- **Config**: Set `OLLAMA_BASE_URL_SCAMMER`, `OLLAMA_BASE_URL_VICTIM`, etc.

---

## 📊 Performance Metrics

### Tracked Metrics
1. **Trust Dynamics**: Turn-by-turn trust changes
2. **Agent Scores**: 0-100 for scammer and expert
3. **Key Moments**: Critical turning points in conversation
4. **Outcome**: Success/failure/uncertain

### Scoring Criteria
- **Scammer**: Persuasiveness, credibility, pressure, consistency
- **Expert**: Intervention effectiveness, clarity, empathy, timing

---

## 🔧 Configuration

### Environment Variables (`.env`)
```bash
# Model Configuration
AGENT_MODEL=gemma3:4b
OLLAMA_BASE_URL=http://127.0.0.1:11434

# Per-Agent Models (optional)
AGENT_MODEL_SCAMMER=gemma3:4b
AGENT_MODEL_VICTIM=gemma3:4b
AGENT_MODEL_EXPERT=gemma3:4b
AGENT_MODEL_RECORDER=gemma3:4b

# Auto-training
AUTO_TRAIN_ENABLED=true

# GPU (Docker)
FORCE_GPU=1

# Logging
LOG_LEVEL=info
```

---

## 🚀 Startup Flow

### Local Development
```bash
1. Install Ollama → Pull models (gemma3:4b)
2. pip install -r backend/requirements.txt
3. Create .env file
4. python start_server.py
5. Open http://127.0.0.1:8000
```

### Docker Deployment
```bash
1. docker compose up -d  # Full containerization
   OR
   docker compose -f docker-compose.local.yml up -d  # Use host Ollama
2. Wait for health checks
3. Access http://localhost:8000
```

---

## 📁 Project Structure

```
AI-Agentv4/
├── backend/
│   ├── agents/          # AI Agent definitions (ADK)
│   │   ├── victim.py
│   │   ├── scammer.py
│   │   ├── expert.py
│   │   └── recorder.py
│   ├── api/             # FastAPI routes
│   │   ├── game_routes_v2.py
│   │   ├── simulation_routes.py
│   │   ├── personal_chat_routes.py
│   │   └── websocket_manager.py
│   ├── services/        # Business logic
│   │   ├── agent_service.py
│   │   ├── simulation_runner.py
│   │   └── rag_service.py
│   ├── utils/           # Utilities
│   │   ├── performance_tracker.py
│   │   ├── role_enforcer.py
│   │   ├── validation.py         # ✨ NEW
│   │   └── context_manager.py
│   ├── llms/            # LLM wrappers
│   │   └── ollama_llm.py
│   ├── db/              # Databases
│   │   └── chroma_db/
│   ├── tests/           # Test suite ✨ NEW
│   │   ├── test_performance_tracker.py
│   │   ├── test_role_enforcer.py
│   │   ├── conftest.py
│   │   └── __init__.py
│   ├── exceptions.py    # Custom exceptions ✨ NEW
│   ├── config.py        # Configuration ✨ NEW
│   ├── main.py          # FastAPI app entry
│   ├── requirements.txt
│   ├── requirements-test.txt  # ✨ NEW
│   └── pytest.ini       # ✨ NEW
├── frontend/            # Web UI
│   ├── index.html
│   ├── css/
│   └── js/
├── rpg_maker_plugins/   # RPG Maker integration
│   ├── SimulationTraining.js
│   └── AI_Bridge.js
├── docker-compose.yml   # Docker config
├── Dockerfile           # Multi-stage build
├── README.md
├── ARCHITECTURE_DOCUMENTATION.md        # ✨ UPDATED
├── PROJECT_EVALUATION_AND_RECOMMENDATIONS.md  # ✨ UPDATED
├── CODE_QUALITY_IMPROVEMENTS.md         # ✨ NEW
├── QUICK_START_IMPROVEMENTS.md          # ✨ NEW
└── IMPROVEMENT_SUMMARY.md               # ✨ NEW
```

---

## 🔐 Security & Privacy

### Data Isolation
- **Offline Mode**: All data stays local (no external API calls)
- **Local LLM**: Ollama runs on-premise (no data sent to cloud)
- **GPU Enforcement**: Can force GPU-only mode (no CPU fallback)

### Checks
- `check_offline_mode()`: Ensures no internet access
- `check_data_isolation()`: Verifies data stays local
- `verify_ollama_local_only()`: Confirms Ollama is local

---

## 🎯 Key Design Decisions

1. **Google ADK**: Chosen for structured agent framework with tool support
2. **Ollama**: Local LLM deployment for privacy and cost savings
3. **Multi-Agent**: Realistic 3-way dialogue (scammer vs victim vs expert)
4. **Trust System**: Gradual, realistic trust changes (not binary)
5. **Role Enforcement**: Prevents AI "character breaking"
6. **RAG**: Evidence-based responses using real scam cases
7. **Docker**: Easy deployment with GPU support

---

## 📚 API Endpoints Summary

### Simulation
- `POST /simulation/start` - Start auto simulation
- `POST /simulation/stop/{id}` - Stop simulation
- `WS /ws/simulation/{id}` - Real-time events

### Game (RPG)
- `POST /api/game/v2/start` - Start game session
- `POST /api/game/v2/message` - Send message to AI
- `GET /api/game/v2/history/{session_id}` - Get conversation history

### Personal Chat
- `POST /api/personal-chat/start` - Start 1-on-1 chat
- `POST /api/personal-chat/message` - Send message
- `POST /api/personal-chat/end` - End session

### Training Data
- `GET /api/training/data` - List training data
- `GET /api/training/data/{filename}` - Download specific file

---

## 🔮 Future Enhancements

1. **Vision Support**: Analyze phishing images (partially implemented)
2. **Voice I/O**: Speech-to-text and text-to-speech
3. **Model Fine-tuning**: Train custom models on collected data
4. **Arms Race System**: Evolve scammer and expert strategies
5. **A/B Testing**: Compare different agent versions
6. **Multi-language**: Support English, Mandarin

---

## 📊 Code Quality Metrics ✨ **NEW**

### Current Status

| Metric | Value | Status |
|--------|-------|--------|
| **Test Coverage** | 100+ tests | ✅ Excellent |
| **Exception Classes** | 20+ custom | ✅ Excellent |
| **Configuration** | Centralized | ✅ Excellent |
| **Input Validation** | Comprehensive | ✅ Excellent |
| **Rate Limiting** | Implemented | ✅ Good |
| **Magic Numbers** | 0 | ✅ Excellent |
| **Code Quality Rating** | ⭐⭐⭐⭐☆ (4/5) | ✅ Good |

### Improvements Made (2026-02-03)

1. ✅ **Custom Exceptions** - 20+ specific exception classes
2. ✅ **Configuration Management** - 8 config modules, no magic numbers
3. ✅ **Input Validation** - Pydantic models, prompt injection detection
4. ✅ **Rate Limiting** - 10 requests per 60 seconds
5. ✅ **Test Suite** - 100+ unit tests with fixtures
6. ✅ **Refactored Code** - performance_tracker.py uses config
7. ✅ **Documentation** - 5 comprehensive markdown documents

### Next Steps

**Phase 2: Security Hardening** (Week 2)
- [ ] Add authentication (JWT)
- [ ] Implement HTTPS enforcement
- [ ] Add audit logging
- [ ] Sanitize PII in logs

**Phase 3: Scalability** (Month 1)
- [ ] Migrate to async database
- [ ] Add Redis caching
- [ ] Implement connection pooling
- [ ] Load balancing for Ollama

**Phase 4: Testing Expansion** (Month 1)
- [ ] Integration tests for API routes
- [ ] E2E tests for critical flows
- [ ] Load testing

---

**Document Version**: 2.0 ✨ **UPDATED**  
**Last Updated**: 2026-02-03  
**Author**: AI-Agentv4 Development Team  
**Changes**: Added code quality infrastructure section
