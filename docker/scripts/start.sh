#!/bin/bash
# Universal startup script — works for local, GCP, and AWS deployments
set -e

echo "================================================"
echo "AI Anti-Fraud Platform Starting..."
echo "================================================"
echo "Time:       $(date)"
echo "Python:     $(python --version)"
echo "User:       $(whoami)"
echo "APP_ENV:    ${APP_ENV:-production}"
echo "PORT:       ${PORT:-8000}"

# ── GPU check (non-fatal) ──────────────────────────
if command -v nvidia-smi &>/dev/null; then
    echo "GPU: $(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null || echo 'detected')"
else
    echo "GPU: not available (CPU mode)"
fi

# ── Wait for Ollama if using it ────────────────────
if [ "${GEMINI_ENABLED:-false}" = "false" ] || [ "${GEMINI_ENABLED:-false}" = "False" ]; then
    OLLAMA_URL="${OLLAMA_BASE_URL:-http://ollama:11434}"
    echo "Waiting for Ollama at ${OLLAMA_URL}..."
    max_attempts=60
    attempt=0
    until curl -sf "${OLLAMA_URL}/api/tags" >/dev/null 2>&1; do
        attempt=$((attempt + 1))
        if [ $attempt -ge $max_attempts ]; then
            echo "ERROR: Ollama not ready after ${max_attempts} attempts. Exiting."
            exit 1
        fi
        [ $((attempt % 10)) -eq 0 ] && echo "  attempt ${attempt}/${max_attempts}..."
        sleep 2
    done
    echo "Ollama ready."
else
    echo "Gemini mode — skipping Ollama wait."
fi

echo "================================================"
echo "Starting uvicorn on 0.0.0.0:${PORT:-8000}"
echo "================================================"

exec uvicorn main:app \
    --host 0.0.0.0 \
    --port "${PORT:-8000}" \
    --log-level "${LOG_LEVEL:-info}" \
    --workers 1
