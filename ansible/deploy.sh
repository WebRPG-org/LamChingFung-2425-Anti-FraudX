#!/bin/bash
# Quick deployment script for Hong Kong Anti-Scam RPG

set -e

echo "🚀 Hong Kong Anti-Scam RPG - Quick Deployment"
echo "=============================================="
echo ""

# Check if Ansible is installed
if ! command -v ansible &> /dev/null; then
    echo "❌ Ansible is not installed. Installing..."
    pip install ansible
fi

# Check if inventory exists
if [ ! -f "inventory/hosts.yml" ]; then
    echo "❌ Inventory file not found. Please configure inventory/hosts.yml first."
    exit 1
fi

# Parse command line arguments
PLAYBOOK="site.yml"
EXTRA_ARGS=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --frontend)
            PLAYBOOK="frontend.yml"
            shift
            ;;
        --backend)
            PLAYBOOK="backend.yml"
            shift
            ;;
        --dev)
            PLAYBOOK="dev-setup.yml"
            shift
            ;;
        --update)
            PLAYBOOK="update.yml"
            shift
            ;;
        --check)
            EXTRA_ARGS="$EXTRA_ARGS --check"
            shift
            ;;
        --verbose)
            EXTRA_ARGS="$EXTRA_ARGS -vvv"
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--frontend|--backend|--dev|--update] [--check] [--verbose]"
            exit 1
            ;;
    esac
done

echo "📋 Running playbook: $PLAYBOOK"
echo ""

# Run Ansible playbook
ansible-playbook -i inventory/hosts.yml playbooks/$PLAYBOOK $EXTRA_ARGS

echo ""
echo "✅ Deployment completed!"
echo ""
echo "Next steps:"
echo "1. Check the application status"
echo "2. Configure DNS if needed"
echo "3. Set up SSL certificates"
echo "4. Monitor logs in /var/log/hk-antiscam-rpg/"
