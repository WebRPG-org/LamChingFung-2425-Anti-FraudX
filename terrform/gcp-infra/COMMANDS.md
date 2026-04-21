# GCP Infrastructure Commands

## Purpose
Deploy the GCP infrastructure layer only.

This module provisions:
- APIs
- VPC and subnets
- GKE cluster
- Cloud SQL
- IAM / service account wiring
- Cloud DNS managed zone

## Before apply
- GCP login is valid
- ADC is configured
- Billing is enabled
- `terraform.tfvars` is ready

## Commands
```bash
cd terrform/gcp-infra
terraform init -upgrade
terraform plan
terraform apply -auto-approve
```

## Verify
```bash
gcloud container clusters list --project <project_id>
gcloud sql instances list --project <project_id>
```

## Important outputs for `gcp-app`
Capture these after apply:
- cluster name
- cluster location
- service account email
- service account name
- Cloud SQL private IP
- DNS zone name
