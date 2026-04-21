# Terraform Deployment Guide

This folder contains the Terraform modules used to deploy `Anti-FraudX` across local Kubernetes, AWS, Azure, GCP, and the final global DNS failover layer.

## Folder layout
- `local-k8s/` - local Kubernetes deployment for development and fallback testing
- `aws-infra/` - AWS infrastructure layer
- `aws-app/` - AWS Kubernetes application layer
- `azure-infra/` - Azure infrastructure layer
- `azure-app/` - Azure Kubernetes application layer
- `gcp-infra/` - GCP infrastructure layer
- `gcp-app/` - GCP Kubernetes application layer
- `global-dns/` - Route53 global failover DNS layer
- `shared/` - shared Kubernetes TLS / issuer assets

## Architecture summary
The same backend application is deployed across multiple cloud providers with cloud-specific integrations:
- AWS: EKS + RDS PostgreSQL + Bedrock
- Azure: AKS + Azure Database for PostgreSQL + Azure OpenAI
- GCP: GKE + Cloud SQL + Vertex AI

The final public global entrypoint is managed by `global-dns/`.

## Suggested apply order
1. `local-k8s/` for local verification
2. `gcp-infra/`
3. `gcp-app/`
4. `aws-infra/`
5. `aws-app/`
6. `azure-infra/`
7. `azure-app/`
8. `global-dns/`

Always apply `global-dns/` last, after all cloud endpoints are already healthy and returning `200 OK` on `/health`.

## Shared deployment principles
- One backend codebase
- One container image pattern
- Managed PostgreSQL in cloud environments
- Kubernetes Secret for runtime-sensitive configuration
- Ingress for public access
- HPA for application-level autoscaling
- Per-cloud logging integration
- TLS on cloud environments

## Important repository note
Real `terraform.tfvars`, Terraform state files, local auth files, and certificates should not be committed to GitHub.
Use `.gitignore` and provide safe example values instead.

## Supporting documents
- `APPLY_CHECKLIST.md`
- `DEPLOYMENT_NOTES.md`
- `DEMO_SCRIPT.md`
- `RUBRIC_MAPPING.md`
- `SECRETS_STRATEGY.md`
- `LOGGING_EVIDENCE.md`
- `REPORT_TEMPLATE.md`
