# Hong Kong Anti-Scam RPG - Ansible Deployment

This directory contains Ansible playbooks for automated deployment of the Hong Kong Anti-Scam RPG training system across multiple computers.

## Prerequisites

### On Control Machine (Your Computer)
```bash
# Install Ansible
pip install ansible

# Or on Windows with WSL/Git Bash
pip install ansible
```

### On Target Machines
- SSH access enabled
- Python 3.8+ installed
- User with sudo privileges

## Quick Start

### 1. Configure Inventory
Edit `inventory/hosts.yml` with your target machines:

```yaml
all:
  children:
    game_servers:
      hosts:
        server1:
          ansible_host: 192.168.1.10
        server2:
          ansible_host: 192.168.1.11
```

### 2. Configure Variables
Edit `group_vars/all.yml` to customize installation settings.

### 3. Run Deployment

**Full Installation (Frontend + Backend + Database):**
```bash
ansible-playbook -i inventory/hosts.yml playbooks/site.yml
```

**Frontend Only:**
```bash
ansible-playbook -i inventory/hosts.yml playbooks/frontend.yml
```

**Backend Only:**
```bash
ansible-playbook -i inventory/hosts.yml playbooks/backend.yml
```

**Development Environment:**
```bash
ansible-playbook -i inventory/hosts.yml playbooks/dev-setup.yml
```

## Playbooks

- `site.yml` - Complete installation (all components)
- `frontend.yml` - RPG game frontend only
- `backend.yml` - AI backend API only
- `dev-setup.yml` - Development environment setup
- `update.yml` - Update existing installation

## Roles

- `common` - Base system setup (Node.js, Python, Git)
- `frontend` - RPG game frontend deployment
- `backend` - AI backend API deployment
- `database` - Database setup (if needed)
- `nginx` - Web server configuration

## Directory Structure

```
ansible/
├── README.md
├── ansible.cfg
├── inventory/
│   ├── hosts.yml
│   └── group_vars/
│       └── all.yml
├── playbooks/
│   ├── site.yml
│   ├── frontend.yml
│   ├── backend.yml
│   ├── dev-setup.yml
│   └── update.yml
└── roles/
    ├── common/
    ├── frontend/
    ├── backend/
    ├── database/
    └── nginx/
```

## Configuration Variables

Key variables in `group_vars/all.yml`:

```yaml
# Application settings
app_name: hk-antiscam-rpg
app_user: rpgadmin
install_dir: /opt/{{ app_name }}

# Frontend settings
frontend_port: 3000
frontend_domain: rpg.example.com

# Backend settings
backend_port: 5000
backend_api_key: your-secret-key

# Node.js version
nodejs_version: "20.x"

# Python version
python_version: "3.11"
```

## Examples

### Deploy to Single Server
```bash
ansible-playbook -i inventory/hosts.yml playbooks/site.yml --limit server1
```

### Deploy with Custom Variables
```bash
ansible-playbook -i inventory/hosts.yml playbooks/site.yml -e "frontend_port=8080"
```

### Check Mode (Dry Run)
```bash
ansible-playbook -i inventory/hosts.yml playbooks/site.yml --check
```

### Verbose Output
```bash
ansible-playbook -i inventory/hosts.yml playbooks/site.yml -vvv
```

## Troubleshooting

### SSH Connection Issues
```bash
# Test connection
ansible all -i inventory/hosts.yml -m ping

# Use password authentication
ansible-playbook -i inventory/hosts.yml playbooks/site.yml --ask-pass
```

### Permission Issues
```bash
# Use sudo
ansible-playbook -i inventory/hosts.yml playbooks/site.yml --become --ask-become-pass
```

## Security Notes

- Store sensitive data in Ansible Vault
- Use SSH keys instead of passwords
- Restrict file permissions on inventory files
- Use firewall rules to limit access

## Support

For issues or questions, refer to the main project documentation.
