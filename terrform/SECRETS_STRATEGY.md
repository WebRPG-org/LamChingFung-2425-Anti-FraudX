# Secrets Strategy

This document explains how secrets and credentials should be handled across Terraform modules.

## Core rules
- Do not commit real secrets to GitHub
- Keep real `terraform.tfvars` out of version control
- Use Kubernetes Secret for runtime-sensitive values
- Prefer cloud-native identity where possible

## Local Kubernetes
- Database URL stored in Kubernetes Secret
- Local development may use mounted credentials only when necessary

## GCP
- Database connection stored in Kubernetes Secret
- Vertex AI should prefer Workload Identity over static JSON keys

## AWS
- Database connection stored in Kubernetes Secret
- AWS runtime auth should prefer IAM roles / IRSA over static AWS keys

## Azure
- Database connection stored in Kubernetes Secret
- Azure OpenAI endpoint and key stored in Kubernetes Secret

## Never commit
- real DB passwords
- cloud API keys
- AWS access keys
- GCP service account JSON
- Azure OpenAI keys
- real Terraform state files
- real `terraform.tfvars`

## Recommended Git workflow
Commit:
- Terraform code
- example configuration
- documentation

Do not commit:
- real runtime secrets
- local credentials
- local kubeconfig
- Terraform state
