# AI-Agents

Getting Started (for first time)
make sure installed below software

    1. Python
    2. Docker
    3. git
    2. Node.js


# 1. Clone repo

bash

    git clone https://github.com/LamChingFung-2425/AI-Agent.git

    cd AI-AGENT


# 2. Setup backend

bash

    cd backend

    python -m venv .venv

    #Windows:

    .\.venv\Scripts\activate

    #macOS/Linux:

    source .venv/bin/activate

    #make sure showed up (.venv) in terminal

    pip install -r requirements.txt

    
    cp .env.example .env

    #replace your own GCP API key in .env

    #GOOGLE_API_KEY="xxxxxxxxxxxxxxxxxxxx"


# 3. Setup frontend

    cd ../frontend

    npm install

# Run docker

bash

    docker-compose up --build

    uvicorn app.main.app --reload

    #fastapi server auto reload

