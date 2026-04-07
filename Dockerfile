FROM python:3.11-slim

WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    && rm -rf /var/lib/apt/lists/*

# 複製requirements文件
COPY backend/requirements.txt .

# 安裝Python依賴
RUN pip install --no-cache-dir -r requirements.txt

# 複製整個後端代碼
COPY backend/ .

# 複製前端代碼
COPY frontend/ ../frontend/
COPY rpg-platform-v2/ ../rpg-platform-v2/

# 暴露端口
EXPOSE 8080

# 健康檢查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/health')" || exit 1

# 啟動應用
CMD ["python", "main.py"]
