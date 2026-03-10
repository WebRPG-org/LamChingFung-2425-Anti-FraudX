# ============================================================
# AI Anti-Fraud Platform — Multi-Stage Dockerfile
# Supports: Local (CPU/GPU), GCP Cloud Run, AWS ECS/App Runner
# ============================================================

# ── Stage 1: base ───────────────────────────────────────────
# Use CUDA base for GPU support; falls back to CPU automatically
FROM nvidia/cuda:12.4.1-cudnn-runtime-ubuntu22.04 AS base

ARG PYTHON_VERSION=3.10
ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.10 \
    python3.10-venv \
    python3-pip \
    curl \
    wget \
    git \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && ln -sf /usr/bin/python3.10 /usr/bin/python \
    && ln -sf /usr/bin/python3.10 /usr/bin/python3 \
    && python -m pip install --no-cache-dir --upgrade pip setuptools wheel

# ── Stage 2: dependencies ───────────────────────────────────
FROM base AS dependencies

COPY backend/requirements.txt /tmp/requirements.txt

# Filter Windows-only packages and install
RUN python3 - <<'PY'
import codecs

src = '/tmp/requirements.txt'
dst = '/tmp/requirements.filtered'

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
with open(dst, 'w', encoding='utf-8') as f:
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith('#'):
            continue
        if any(s.lower().startswith(p) for p in windows_only):
            continue
        f.write(line + '\n')
print('Filtered requirements written.')
PY

RUN pip install --no-cache-dir -r /tmp/requirements.filtered \
    && rm -f /tmp/requirements.txt /tmp/requirements.filtered

# ── Stage 3: final ──────────────────────────────────────────
FROM base AS final

# Copy installed packages from dependencies stage
COPY --from=dependencies /usr/local/lib/python3.10/dist-packages /usr/local/lib/python3.10/dist-packages
COPY --from=dependencies /usr/local/bin /usr/local/bin

# Runtime tools
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Non-root user
RUN groupadd -r appuser && useradd -r -g appuser -u 1000 appuser

# Application directories
RUN mkdir -p \
    /app/backend/training_data \
    /app/backend/training_data/fine_tuning_data \
    /app/backend/models \
    /app/backend/db \
    /app/backend/logs \
    /app/backend/agents/backups \
    && chown -R appuser:appuser /app

# Application code
COPY --chown=appuser:appuser backend/  /app/backend/
COPY --chown=appuser:appuser frontend/ /app/frontend/
COPY --chown=appuser:appuser rpg-platform-v2/ /app/rpg-platform-v2/

# Environment defaults (overridable at runtime)
ENV PYTHONPATH=/app/backend \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    APP_ENV=production \
    LOG_LEVEL=info \
    PORT=8000

# Startup script
COPY --chown=appuser:appuser docker/scripts/start.sh /app/start.sh
RUN chmod +x /app/start.sh

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

USER appuser
WORKDIR /app

CMD ["/app/start.sh"]
