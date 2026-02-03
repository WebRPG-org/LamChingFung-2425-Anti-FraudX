FROM nvidia/cuda:12.4.1-cudnn-runtime-ubuntu22.04

# Install system dependencies
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Ollama
RUN curl -fsSL https://ollama.ai/install.sh | sh

# Set environment variables for CUDA support
ENV OLLAMA_HOST=0.0.0.0 \
    OLLAMA_ORIGINS=* \
    OLLAMA_NUM_PARALLEL=2 \
    OLLAMA_MAX_LOADED_MODELS=2 \
    OLLAMA_KEEP_ALIVE=5m \
    PATH=/usr/local/nvidia/bin:/usr/local/cuda/bin:${PATH} \
    LD_LIBRARY_PATH=/usr/local/nvidia/lib:/usr/local/nvidia/lib64:${LD_LIBRARY_PATH}

# Create ollama user and directories
RUN useradd -r -s /bin/false -u 1000 ollama && \
    mkdir -p /root/.ollama && \
    chown -R ollama:ollama /root/.ollama

# Expose Ollama port
EXPOSE 11434

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
    CMD curl -f http://localhost:11434/api/tags || exit 1

# Create startup script with GPU detection
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
echo "================================================"\n\
echo "🚀 Ollama 服务启动中..."\n\
echo "================================================"\n\
echo ""\n\
\n\
# Check for NVIDIA GPU\n\
if command -v nvidia-smi &> /dev/null; then\n\
    echo "✅ NVIDIA GPU 检测:"\n\
    nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader || echo "   ⚠️  无法查询GPU详情"\n\
    echo ""\n\
    echo "🔧 CUDA 环境:"\n\
    echo "   CUDA_VISIBLE_DEVICES: ${CUDA_VISIBLE_DEVICES:-all}"\n\
    echo "   NVIDIA_VISIBLE_DEVICES: ${NVIDIA_VISIBLE_DEVICES:-all}"\n\
else\n\
    echo "⚠️  警告: nvidia-smi 不可用"\n\
    echo "   Ollama 将在 CPU 模式下运行"\n\
fi\n\
\n\
echo ""\n\
echo "📊 Ollama 配置:"\n\
echo "   Host: ${OLLAMA_HOST}"\n\
echo "   Max Models: ${OLLAMA_MAX_LOADED_MODELS}"\n\
echo "   Keep Alive: ${OLLAMA_KEEP_ALIVE}"\n\
echo ""\n\
echo "🌐 启动 Ollama 服务..."\n\
echo "================================================"\n\
echo ""\n\
\n\
exec ollama serve\n\
' > /usr/local/bin/start-ollama.sh && \
    chmod +x /usr/local/bin/start-ollama.sh

# Start Ollama with the startup script
CMD ["/usr/local/bin/start-ollama.sh"]
