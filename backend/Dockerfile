FROM python:3.11-slim

# set working directory
WORKDIR /app

# install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    && rm -rf /var/lib/apt/lists/*

# install Google Chrome (for SFC scraper)
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-chrome-keyring.gpg && \
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome-keyring.gpg] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list && \
    apt-get update && \
    apt-get install -y google-chrome-stable --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# install Python dependencies
RUN pip install --cache-dir /tmp/pip-cache -r requirements.txt


COPY ./app ./app

# set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV LIGHTWEIGHT_MODE=true
ENV DOCKER_ENV=true


EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]