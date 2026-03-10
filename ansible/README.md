# AI Anti-Fraud Platform — Ansible Deployment

> Version: 4.1 | Updated: 2026-03-11

Automated deployment for local servers, GCP, and AWS. Supports both **Ollama** (local GPU) and **Gemini API** (cloud) modes.

---

## Quick Start

### Prerequisites

```bash
# Install Ansible (on your control machine)
pip install ansible

# On Windows: use WSL or Git Bash
```

### 1. Configure Inventory

```bash
cp ansible/inventory/hosts.example.yml ansible/inventory/hosts.yml
# Edit hosts.yml with your server IPs and settings
```

### 2. Set Secrets (Ansible Vault)

```bash
# Create encrypted secrets file
ansible-vault create ansible/inventory/group_vars/vault.yml

# Add:
vault_gemini_api_key: "your-gemini-api-key"
```

### 3. Deploy

```bash
# Full local deployment (Ollama mode)
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/site.yml

# Full deployment (Gemini mode)
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/site.yml \
  -e "gemini_enabled=true gemini_api_key=your_key"

# GCP deployment
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/deploy-gcp.yml

# AWS deployment
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/deploy-aws.yml
```

---

## Playbooks

| Playbook | Purpose | Command |
|----------|---------|--------|
| `site.yml` | Full deployment (all components) | `ansible-playbook ... playbooks/site.yml` |
| `update.yml` | Update existing installation | `ansible-playbook ... playbooks/update.yml` |
| `deploy-gcp.yml` | GCP-specific deployment | `ansible-playbook ... playbooks/deploy-gcp.yml` |
| `deploy-aws.yml` | AWS-specific deployment | `ansible-playbook ... playbooks/deploy-aws.yml` |

---

## Roles

| Role | Purpose | Condition |
|------|---------|----------|
| `common` | Python 3.10, Node.js, NVIDIA toolkit, directories, firewall | Always |
| `ollama` | Install Ollama, pull models, systemd service, warm-up | `gemini_enabled=false` |
| `backend` | Clone repo, venv, pip install, build frontend, systemd service | Always |
| `nginx` | Reverse proxy, WebSocket support, optional SSL/Let's Encrypt | `nginx_install=true` |

---

## LLM Mode Selection

### Ollama (local GPU — default)

```yaml
# group_vars/all.yml or host var
gemini_enabled: false
ollama_model: gemma3:4b
nvidia_gpu: true      # installs NVIDIA Container Toolkit
```

### Gemini API (cloud — recommended for GCP/AWS)

```yaml
gemini_enabled: true
gemini_api_key: "{{ vault_gemini_api_key }}"
gemini_model_scammer: gemini-2.5-flash
gemini_model_expert: gemini-2.5-flash
```

---

## Key Variables (`group_vars/all.yml`)

| Variable | Default | Description |
|----------|---------|-------------|
| `gemini_enabled` | `false` | Use Gemini API instead of Ollama |
| `ollama_model` | `gemma3:4b` | Default Ollama model |
| `ollama_models_to_pull` | `[gemma3:4b]` | Models to pull at deploy time |
| `nvidia_gpu` | `false` | Install NVIDIA Container Toolkit |
| `backend_port` | `8000` | FastAPI port |
| `app_domain` | `antiscam.example.com` | Domain for nginx |
| `enable_ssl` | `false` | Enable Let's Encrypt SSL |
| `nginx_install` | `true` | Install nginx reverse proxy |
| `deploy_mode` | `local` | `local` / `gcp` / `aws` |

---

## Directory Structure

```
ansible/
├── ansible.cfg
├── inventory/
│   ├── hosts.yml              # Your server list (git-ignored)
│   ├── hosts.example.yml      # Example — copy and edit
│   └── group_vars/
│       ├── all.yml            # Global variables
│       └── vault.yml          # Encrypted secrets (ansible-vault)
├── playbooks/
│   ├── site.yml               # Full deployment
│   ├── update.yml             # Update existing
│   ├── deploy-gcp.yml         # GCP-specific
│   └── deploy-aws.yml         # AWS-specific
└── roles/
    ├── common/                # Base system setup
    ├── ollama/                # Ollama LLM service
    ├── backend/               # FastAPI backend
    └── nginx/                 # Nginx reverse proxy
```

---

## Common Commands

```bash
# Dry run (check mode)
ansible-playbook -i inventory/hosts.yml playbooks/site.yml --check

# Single host
ansible-playbook -i inventory/hosts.yml playbooks/site.yml --limit server1

# Single role
ansible-playbook -i inventory/hosts.yml playbooks/site.yml --tags backend

# With vault password
ansible-playbook -i inventory/hosts.yml playbooks/site.yml --ask-vault-pass

# Test SSH connectivity
ansible all -i inventory/hosts.yml -m ping

# View logs on remote
ansible all -i inventory/hosts.yml -m shell -a "tail -50 /var/log/ai-antiscam/backend.log"

# Restart backend only
ansible all -i inventory/hosts.yml -m systemd -a "name=ai-antiscam-backend state=restarted" --become

# Pull new Ollama model
ansible all -i inventory/hosts.yml -m command -a "ollama pull gemma3:4b" --become
```

---

## After Deployment

| URL | Purpose |
|-----|---------|
| `http://HOST:8000/` | Main dashboard |
| `http://HOST:8000/rpgv2` | RPGv2 game |
| `http://HOST:8000/docs` | FastAPI Swagger docs |
| `http://HOST:8000/health` | Health check |
| `http://HOST:8000/tools` | Tools Center (scraper/finetune/modelgen) |

---

## Troubleshooting

```bash
# Check service status
systemctl status ai-antiscam-backend
systemctl status ollama

# View logs
journalctl -u ai-antiscam-backend -f
journalctl -u ollama -f
tail -f /var/log/ai-antiscam/backend.log

# Test Ollama
curl http://localhost:11434/api/tags

# Test backend
curl http://localhost:8000/health
```
