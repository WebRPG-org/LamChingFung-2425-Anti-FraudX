#!/bin/bash
# Ollama startup script with GPU detection
set -e

echo "================================================"
echo "Ollama Service Starting..."
echo "================================================"

if command -v nvidia-smi &> /dev/null; then
    echo "GPU detected:"
    nvidia-smi --query-gpu=name,memory.total,driver_version \
        --format=csv,noheader 2>/dev/null || echo "  (unable to query GPU details)"
else
    echo "WARNING: nvidia-smi not available — running in CPU mode"
fi

echo ""
echo "Ollama config:"
echo "  OLLAMA_HOST:              ${OLLAMA_HOST:-0.0.0.0}"
echo "  OLLAMA_NUM_PARALLEL:      ${OLLAMA_NUM_PARALLEL:-2}"
echo "  OLLAMA_MAX_LOADED_MODELS: ${OLLAMA_MAX_LOADED_MODELS:-2}"
echo "  OLLAMA_KEEP_ALIVE:        ${OLLAMA_KEEP_ALIVE:-5m}"
echo ""
echo "Starting ollama serve..."
echo "================================================"

exec ollama serve
