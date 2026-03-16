# AI Anti-Fraud Platform — Docker Deployment Guide

> Version: 4.1 | Last Updated: 2026-03-11

---

## Quick Reference

| Scenario | Command |
|----------|---------|
| Local dev (GPU + Ollama in Docker) | `docker compose up` |
| Local dev (host Ollama or Gemini) | `docker compose -f docker-compose.local.yml up` |
| GCP — Gemini mode | `docker compose -f docker-compose.gcp.yml up` |
| GCP — Ollama mode (GCE GPU) | `docker compose -f docker-compose.gcp.yml --profile ollama up` |
| AWS — Gemini mode | `docker compose -f docker-compose.aws.yml up` |
| AWS — Ollama mode (EC2 GPU) | `docker compose -f docker-compose.aws.yml --profile ollama up` |

---

## Files Overview

```
Dockerfile                  Multi-stage build (CUDA base, CPU fallback)
docker-compose.yml          Local GPU dev (Ollama in container)
docker-compose.local.yml    Local dev (host Ollama or Gemini, no GPU needed)
docker-compose.gcp.yml      GCP: Cloud Run (Gemini) or GCE GPU (Ollama)
docker-compose.aws.yml      AWS: App Runner/ECS (Gemini) or EC2 GPU (Ollama)
.dockerignore               Excludes DB, training data, logs, node_modules
docker/ollama/Dockerfile    Ollama service image (CUDA + GPU detection)
docker/ollama/start-ollama.sh  Ollama startup with GPU info logging
docker/scripts/start.sh     Backend startup (waits for Ollama if needed)
```

---

## 1. Local Development

### Option A: GPU machine with Ollama in Docker

Requires: Docker Desktop + NVIDIA Container Toolkit

```bash
# Build and start everything
docker compose up --build

# Access
# Backend API:  http://localhost:8000
# RPGv2 game:   http://localhost:8000/rpgv2
# API docs:     http://localhost:8000/docs
```

### Option B: Host Ollama or Gemini API (no GPU required)

```bash
# Ollama running on host
docker compose -f docker-compose.local.yml up --build

# Gemini API
GEMINI_ENABLED=true GEMINI_API_KEY=your_key \
  docker compose -f docker-compose.local.yml up --build
```

> **Linux note**: `host.docker.internal` requires the `extra_hosts: host-gateway` entry (already included). On Windows/Mac Docker Desktop it works automatically.

### Environment Variables

Create `backend/.env` with your settings (see `env.example`). The local compose file loads it automatically via `env_file`.

---

## 2. GCP Deployment

### Option A: Cloud Run + Gemini (recommended — serverless, no GPU)

```bash
# 1. Authenticate
gcloud auth configure-docker REGION-docker.pkg.dev

# 2. Build and push to Artifact Registry
export GCP_PROJECT_ID=your-project-id
export GCP_REGION=asia-east1
export IMAGE_TAG=v1.0

docker build -t ${GCP_REGION}-docker.pkg.dev/${GCP_PROJECT_ID}/ai-antiscam/backend:${IMAGE_TAG} .
docker push ${GCP_REGION}-docker.pkg.dev/${GCP_PROJECT_ID}/ai-antiscam/backend:${IMAGE_TAG}

# 3. Deploy to Cloud Run
gcloud run deploy ai-antiscam \
  --image=${GCP_REGION}-docker.pkg.dev/${GCP_PROJECT_ID}/ai-antiscam/backend:${IMAGE_TAG} \
  --region=${GCP_REGION} \
  --platform=managed \
  --allow-unauthenticated \
  --port=8080 \
  --memory=2Gi \
  --cpu=2 \
  --set-env-vars="GEMINI_ENABLED=true,APP_ENV=production" \
  --set-secrets="GEMINI_API_KEY=gemini-api-key:latest"
```

### Option B: GCE with GPU + Ollama

```bash
# 1. Create GPU instance (L4 recommended for gemma3:4b)
gcloud compute instances create ai-antiscam-gpu \
  --zone=asia-east1-c \
  --machine-type=g2-standard-4 \
  --accelerator=type=nvidia-l4,count=1 \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size=100GB

# 2. SSH and install Docker + NVIDIA Container Toolkit
ssh ai-antiscam-gpu
curl -fsSL https://get.docker.com | sh
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
# (follow NVIDIA Container Toolkit install docs)

# 3. Clone repo and start with Ollama
GCP_PROJECT_ID=your-project-id GCP_REGION=asia-east1 \
  docker compose -f docker-compose.gcp.yml --profile ollama up -d
```

---

## 3. AWS Deployment

### Option A: App Runner or ECS Fargate + Gemini (serverless)

```bash
# 1. Authenticate to ECR
export AWS_ACCOUNT_ID=123456789012
export AWS_REGION=ap-east-1
export ECR_REPO=ai-antiscam
export IMAGE_TAG=v1.0

aws ecr get-login-password --region ${AWS_REGION} | \
  docker login --username AWS --password-stdin \
  ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com

# 2. Build and push to ECR
docker build -t ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO}:${IMAGE_TAG} .
docker push ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO}:${IMAGE_TAG}

# 3a. Deploy with App Runner (simplest)
aws apprunner create-service \
  --service-name ai-antiscam \
  --source-configuration "ImageRepository={ImageIdentifier=${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO}:${IMAGE_TAG},ImageRepositoryType=ECR}" \
  --instance-configuration "Cpu=2 vCPU,Memory=4 GB"

# 3b. Or deploy to ECS Fargate using your task definition
# (set GEMINI_API_KEY via Secrets Manager in task definition)
```

### Option B: EC2 GPU + Ollama (g4dn.xlarge or g5.xlarge)

```bash
# 1. Launch EC2 GPU instance
aws ec2 run-instances \
  --image-id ami-xxxxxxxxx \
  --instance-type g4dn.xlarge \
  --key-name your-key \
  --security-group-ids sg-xxxxxxxx \
  --block-device-mappings '[{"DeviceName":"/dev/sda1","Ebs":{"VolumeSize":100}}]'

# 2. Install Docker + NVIDIA Container Toolkit on instance
# 3. Clone repo
# 4. Start with Ollama profile
AWS_ACCOUNT_ID=123456789012 AWS_REGION=ap-east-1 ECR_REPO=ai-antiscam \
  docker compose -f docker-compose.aws.yml --profile ollama up -d

# 5. Pull models
docker exec ai-antiscam-ollama ollama pull gemma3:4b
```

---

## 4. Post-Deploy: Pull Ollama Models

After starting with Ollama profile, pull the required models:

```bash
# Pull default model
docker exec ai-antiscam-ollama ollama pull gemma3:4b

# Optional: pull fine-tuned models created by Tools Center
docker exec ai-antiscam-ollama ollama pull anti-fraud-expert
docker exec ai-antiscam-ollama ollama pull scammer-sim

# Verify
docker exec ai-antiscam-ollama ollama list
```

---

## 5. Health Checks

```bash
# Backend health
curl http://localhost:8000/health

# Ollama health
curl http://localhost:11434/api/tags

# Docker service status
docker compose ps
docker compose logs -f backend
docker compose logs -f ollama
```

---

## 6. Recommended Instance Types

### GCP

| Mode | Instance | vCPU | RAM | GPU | Est. Cost |
|------|----------|------|-----|-----|----------|
| Gemini (Cloud Run) | Serverless | 2 | 2GB | — | Pay per request |
| Ollama (gemma3:4b) | g2-standard-4 | 4 | 16GB | L4 16GB | ~$0.70/hr |
| Ollama (larger model) | g2-standard-8 | 8 | 32GB | L4 24GB | ~$1.20/hr |

### AWS

| Mode | Instance | vCPU | RAM | GPU | Est. Cost |
|------|----------|------|-----|-----|----------|
| Gemini (App Runner) | Serverless | 2 | 4GB | — | Pay per request |
| Ollama (gemma3:4b) | g4dn.xlarge | 4 | 16GB | T4 16GB | ~$0.53/hr |
| Ollama (larger model) | g5.xlarge | 4 | 16GB | A10G 24GB | ~$1.01/hr |

---

## 7. Environment Variables Reference

See `env.example` for the full list. Key variables for cloud deployments:

```bash
# Required for Gemini mode
GEMINI_ENABLED=true
GEMINI_API_KEY=your_key

# Required for Ollama mode (cloud)
GEMINI_ENABLED=false
OLLAMA_BASE_URL=http://ollama:11434

# Performance (already optimised in compose files)
GEMINI_MAX_OUTPUT_TOKENS=800
OLLAMA_NUM_CTX=2048
OLLAMA_NUM_PREDICT=400

# App
APP_ENV=production
LOG_LEVEL=info
PORT=8080              # Cloud Run / ECS use 8080
```
