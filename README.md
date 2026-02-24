# AI-Agent v4 - Scam Detection System

An intelligent multi-agent system for detecting and analyzing scam scenarios using RAG (Retrieval Augmented Generation) technology.

## Features

- **Multi-Agent Architecture**: Scammer, Victim, Expert, and Recorder agents working together
- **RAG Integration**: Efficient context retrieval using ChromaDB vector database
- **Token Optimization**: 99.4% token reduction (139,742 → 824 tokens per request)
- **Gemini API Integration**: Powered by Google's Gemini AI models
- **Real-time Analysis**: WebSocket-based conversation monitoring

## System Requirements

- Python 3.8 or higher
- 4GB RAM minimum (8GB recommended for RAG system)
- Internet connection for Gemini API

## Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd AI-Agentv4
```

### 2. Automated Setup (Recommended)

#### Windows
Double-click `setup.bat` or run:
```cmd
setup.bat
```

#### Cross-Platform
```bash
python setup.py
```

### 3. Manual Setup (Alternative)

#### Windows (PowerShell)

```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install dependencies
cd backend
pip install -r requirements.txt
```

#### Windows (CMD)

```cmd
# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\activate.bat

# Install dependencies
cd backend
pip install -r requirements.txt
```

#### Linux/macOS

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
cd backend
pip install -r requirements.txt
```

### 4. Configure Environment

Edit `backend/.env` (created by setup script):

```env
# Choose your LLM provider
GEMINI_ENABLED=true  # or false for Ollama

# If using Gemini
GEMINI_API_KEY=your_actual_api_key_here

# If using Ollama
OLLAMA_HOST=http://localhost:11434
```

### 5. Run the Application

#### Windows (Recommended)
Double-click `quick_start.bat` - This will:
- Check and create lite data files
- Initialize Gemini files (if enabled) or check Ollama
- Start backend server (port 8000)
- Start RPGv2 frontend (port 3000)

#### Manual Start
```bash
# Activate virtual environment
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/macOS

# Start backend
cd backend
python main.py
```

The server will start at `http://localhost:8000`

## Project Structure

```
AI-Agentv4/
├── backend/
│   ├── agents/           # Agent implementations
│   │   ├── scammer.py
│   │   ├── victim.py
│   │   ├── expert.py
│   │   └── recorder.py
│   ├── llms/            # LLM factory and configurations
│   │   └── llm_factory.py
│   ├── rag/             # RAG system
│   │   ├── rag_helper.py
│   │   └── chroma_db/   # Vector database storage
│   ├── scripts/         # Utility scripts
│   │   ├── init_rag.py
│   │   └── test_rag_integration.py
│   ├── knowledge/       # Knowledge base files
│   ├── requirements.txt # Python dependencies
│   └── main.py         # Application entry point
├── .env.example        # Environment template
├── .gitignore
├── setup.py           # Automated setup script
└── README.md
```

## RAG System

The RAG (Retrieval Augmented Generation) system provides efficient context retrieval:

- **Vector Database**: ChromaDB for similarity search
- **Embeddings**: Sentence Transformers for text vectorization
- **Similarity Threshold**: 10.0 (configurable)
- **Token Reduction**: 99.4% reduction compared to file uploads

### Testing RAG Integration

```bash
cd backend
python scripts/test_rag_integration.py
```

## API Endpoints

- `GET /` - Health check
- `POST /api/conversation/start` - Start new conversation
- `WS /ws/conversation/{conversation_id}` - WebSocket for real-time updates

## Development

### Running Tests

```bash
pytest backend/scripts/test_rag_integration.py -v
```

### Deactivating Virtual Environment

```bash
deactivate
```

## Troubleshooting

### Gemini API Quota Exceeded

If you see `429 RESOURCE_EXHAUSTED` error:
- Free tier: 20 requests/day
- Wait for quota reset (daily)
- Consider upgrading to paid tier

### ChromaDB Issues

If RAG system fails to initialize:
```bash
pip install --upgrade chromadb sentence-transformers
```

### Import Errors

Make sure virtual environment is activated:
```bash
# Windows PowerShell
.\venv\Scripts\Activate.ps1

# Linux/macOS
source venv/bin/activate
```

## Performance

- **Token Usage**: ~824 tokens per request (with RAG)
- **Response Time**: < 2 seconds (typical)
- **Memory Usage**: ~500MB (with ChromaDB loaded)

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]

## Support

For issues and questions, please open an issue on GitHub.
