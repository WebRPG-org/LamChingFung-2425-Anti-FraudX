# syntax=docker/dockerfile:1.7-labs
# AI 反詐騙模擬訓練平台 - Docker配置（優化快取與建置時間）
FROM nvidia/cuda:12.4.1-cudnn-runtime-ubuntu22.04

# 設置工作目錄
WORKDIR /app

# 安裝系統依賴
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y \
    python3 python3-venv python3-pip \
    curl wget git build-essential \
    && rm -rf /var/lib/apt/lists/*

# 安裝 Ollama
RUN curl -fsSL https://ollama.ai/install.sh | sh

# 先僅複製依賴清單，讓 pip 充分利用層快取
COPY backend/requirements.txt ./requirements.txt

# 安裝 Python 依賴（過濾 Windows 專用套件）
RUN python3 - <<'PY'
import sys, io, codecs
src = 'requirements.txt'
dst = '/tmp/requirements.filtered'
# Read raw bytes and detect UTF-16 by presence of NUL bytes or BOM
raw = open(src, 'rb').read()
text = None
if raw.startswith(codecs.BOM_UTF16_LE) or raw.startswith(codecs.BOM_UTF16_BE) or b'\x00' in raw:
    for enc in ('utf-16', 'utf-16-le', 'utf-16-be'):
        try:
            text = raw.decode(enc)
            break
        except Exception:
            pass
if text is None:
    text = raw.decode('utf-8', errors='ignore')

windows_only = ('pywin32', 'pyreadline', 'pyreadline3')
with open(dst, 'w', encoding='utf-8') as f_out:
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith('#'):
            f_out.write(line + '\n')
            continue
        low = s.lower()
        if low.startswith(windows_only) or any(low.startswith(p) for p in windows_only):
            continue
        f_out.write(line + '\n')
print('Filtered requirements written to', dst)
PY
RUN --mount=type=cache,target=/root/.cache/pip pip3 install -r /tmp/requirements.filtered

# 複製專案程式碼（這層之後的變更不會使依賴層失效）
COPY backend/ ./backend/
COPY frontend/ ./frontend/
COPY start_server.py ./

# 創建必要的目錄
RUN mkdir -p backend/training_data backend/models backend/db

# 設置環境變量
ENV PYTHONPATH=/app/backend \
    OLLAMA_BASE_URL=http://ollama:11434 \
    AGENT_MODEL=gemma3:27b\
    OLLAMA_LLM_LIBRARY=cuda \
    NVIDIA_VISIBLE_DEVICES=all \
    NVIDIA_DRIVER_CAPABILITIES=compute,utility

# 暴露端口
EXPOSE 8000 11434

# 創建啟動腳本（直接以 uvicorn 啟動後端）
RUN echo '#!/bin/bash\nset -e\necho "🚀 啟動 AI 反詐騙模擬訓練平台"\necho "======================================"\necho "🌐 啟動 Web 服務..."\ncd /app/backend\nexec uvicorn main:app --host 0.0.0.0 --port 8000\n' > /app/start.sh && chmod +x /app/start.sh

# 健康檢查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# 啟動命令
CMD ["/app/start.sh"]
