FROM python:3.11-slim

WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 複製 requirements
COPY requirements.txt .

# 安裝 Python 依賴
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用代碼
COPY backend/ ./backend/
COPY rpg-platform-v2/ ./rpg-platform-v2/
COPY frontend/ ./frontend/

# 設置工作目錄為 backend
WORKDIR /app/backend

# 暴露端口
EXPOSE 8080

# 設置環境變量
ENV PYTHONUNBUFFERED=1
ENV PORT=8080
ENV DEPLOYMENT_ENV=cloud

# 啟動應用
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
