# 多阶段构建 - AI反诈骗训练平台
# Stage 1: Base image with system dependencies
FROM nvidia/cuda:12.4.1-cudnn-runtime-ubuntu22.04 AS base

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    python3.10 \
    python3.10-venv \
    python3-pip \
    curl \
    wget \
    git \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && ln -sf /usr/bin/python3.10 /usr/bin/python \
    && ln -sf /usr/bin/python3.10 /usr/bin/python3

# 升级pip
RUN python -m pip install --no-cache-dir --upgrade pip setuptools wheel

# Stage 2: Dependencies installation
FROM base AS dependencies

# 复制requirements文件
COPY backend/requirements.txt /tmp/requirements.txt

# 过滤Windows专用包并安装依赖
RUN python3 - <<'PY' && \
    pip install --no-cache-dir -r /tmp/requirements.filtered
import codecs

src = '/tmp/requirements.txt'
dst = '/tmp/requirements.filtered'

# 读取并检测编码
raw = open(src, 'rb').read()
text = None

# 尝试UTF-16编码
if raw.startswith(codecs.BOM_UTF16_LE) or raw.startswith(codecs.BOM_UTF16_BE) or b'\x00' in raw:
    for enc in ('utf-16', 'utf-16-le', 'utf-16-be'):
        try:
            text = raw.decode(enc)
            break
        except Exception:
            pass

# 默认UTF-8
if text is None:
    text = raw.decode('utf-8', errors='ignore')

# 过滤Windows专用包
windows_only = ('pywin32', 'pyreadline', 'pyreadline3')
with open(dst, 'w', encoding='utf-8') as f_out:
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith('#'):
            continue
        low = s.lower()
        if any(low.startswith(p) for p in windows_only):
            continue
        f_out.write(line + '\n')

print(f'✅ Filtered requirements written to {dst}')
PY

# Stage 3: Final application image
FROM base AS final

# 从dependencies阶段复制已安装的Python包
COPY --from=dependencies /usr/local/lib/python3.10/dist-packages /usr/local/lib/python3.10/dist-packages
COPY --from=dependencies /usr/local/bin /usr/local/bin

# 创建非root用户
RUN groupadd -r appuser && useradd -r -g appuser -u 1000 appuser

# 创建必要的目录并设置权限
RUN mkdir -p \
    /app/backend/training_data \
    /app/backend/models \
    /app/backend/db \
    /app/backend/arms_race_data \
    /app/backend/agent_versions \
    /app/backend/ab_test_results \
    /app/backend/agents/backups \
    && chown -R appuser:appuser /app

# 复制应用代码
COPY --chown=appuser:appuser backend/ /app/backend/
COPY --chown=appuser:appuser frontend/ /app/frontend/
COPY --chown=appuser:appuser start_server.py /app/

# 设置环境变量
ENV PYTHONPATH=/app/backend \
    PYTHONUNBUFFERED=1 \
    OLLAMA_BASE_URL=http://ollama:11434 \
    AGENT_MODEL=gemma3:4b \
    OLLAMA_LLM_LIBRARY=cuda \
    NVIDIA_VISIBLE_DEVICES=all \
    NVIDIA_DRIVER_CAPABILITIES=compute,utility \
    APP_ENV=production

# 暴露端口
EXPOSE 8000

# 创建启动脚本
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
echo "================================================"\n\
echo "🚀 AI反诈骗训练平台启动中..."\n\
echo "================================================"\n\
echo ""\n\
echo "⏰ 时间: $(date)"\n\
echo "🐍 Python版本: $(python --version)"\n\
echo "📍 工作目录: $(pwd)"\n\
echo "👤 用户: $(whoami)"\n\
echo ""\n\
\n\
# 等待Ollama服务就绪\n\
echo "⏳ 等待Ollama服务就绪..."\n\
echo "   使用URL: ${OLLAMA_BASE_URL}"\n\
max_attempts=30\n\
attempt=0\n\
while [ $attempt -lt $max_attempts ]; do\n\
    if curl -sf ${OLLAMA_BASE_URL}/api/tags > /dev/null 2>&1; then\n\
        echo "✅ Ollama服务已就绪"\n\
        break\n\
    fi\n\
    attempt=$((attempt + 1))\n\
    echo "   尝试 $attempt/$max_attempts..."\n\
    sleep 2\n\
done\n\
\n\
if [ $attempt -eq $max_attempts ]; then\n\
    echo "❌ 警告: Ollama服务未响应，但继续启动..."\n\
fi\n\
\n\
echo ""\n\
echo "🌐 启动Web服务器..."\n\
echo "   地址: http://0.0.0.0:8000"\n\
echo "   环境: ${APP_ENV}"\n\
echo "   模型: ${AGENT_MODEL}"\n\
echo ""\n\
\n\
cd /app/backend\n\
exec uvicorn main:app --host 0.0.0.0 --port 8000 --log-level ${LOG_LEVEL:-info}\n\
' > /app/start.sh && chmod +x /app/start.sh

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 切换到非root用户
USER appuser

# 工作目录
WORKDIR /app

# 启动命令
CMD ["/app/start.sh"]
