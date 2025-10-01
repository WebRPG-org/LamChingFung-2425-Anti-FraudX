# AI-Agent

## Quick Start
### Prerequisites

Ensure installed below software:

1. Python
2. Docker
3. Git
4. Node.js

### Clone the Repository

```bash
git clone https://github.com/LamChingFung-2425/AI-Agent.git
cd AI-Agents
```

### Environment 

```bash
# Copy environment configuration file
cp env.example .env

# Edit configuration file and add your Google API key
nano backend/.env
```

Configure in the `.env` file:

```.env
# Google AI API Key
GOOGLE_API_KEY="Replace to your own API key"


#### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.\.venv\Scripts\activate

# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start backend service
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### Docker
- **backend**: (port 8000)
- **frontend**: (port 5173)
- **mongo**: (port 27017) 
- **redis**: (port 6379) 


### Docker Deployment 

```bash
# Build and start all services
docker-compose up --build

# Run in background
docker-compose up -d --build
```

### Viewing Logs

```bash
# View all service logs
docker-compose logs

# View specific service logs
docker-compose logs backend
docker-compose logs mongo
```



