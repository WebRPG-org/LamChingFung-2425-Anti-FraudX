FROM nvidia/cuda:12.4.1-cudnn-runtime-ubuntu22.04

RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y \
    curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://ollama.ai/install.sh | sh

ENV OLLAMA_HOST=0.0.0.0 \
    OLLAMA_LLM_LIBRARY=cuda

EXPOSE 11434

CMD ["ollama", "serve"]
