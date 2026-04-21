FROM node:20-bullseye AS rpgv2-builder

WORKDIR /build/rpg-platform-v2
COPY rpg-platform-v2/package.json ./package.json
RUN npm install
COPY rpg-platform-v2/ ./
RUN npm run build

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r /app/requirements.txt

COPY . /app
COPY --from=rpgv2-builder /build/rpg-platform-v2/dist /app/rpg-platform-v2/dist

EXPOSE 8080

CMD ["/bin/sh", "-c", "python backend/seed_alerts.py && python backend/main.py"]
