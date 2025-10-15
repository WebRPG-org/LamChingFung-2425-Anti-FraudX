#!/bin/bash
echo "Starting AI-Agent Backend Service..."
cd "$(dirname "$0")/backend"
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
