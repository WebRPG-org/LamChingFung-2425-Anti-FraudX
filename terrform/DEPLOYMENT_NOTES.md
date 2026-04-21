# Deployment Notes

This document records the practical deployment notes for the current Terraform structure.

## Current module structure
The current deployment layout is split by cloud and by layer:
- `aws-infra` and `aws-app`
- `azure-infra` and `azure-app`
- `gcp-infra` and `gcp-app`
- `global-dns`
- `local-k8s`

This split is preferred over older single-folder cloud modules because it keeps infrastructure and application rollout easier to debug.

## Recommended real deployment order
1. Local verification with `local-k8s`
2. GCP infrastructure
3. GCP application
4. AWS infrastructure
5. AWS application
6. Azure infrastructure
7. Azure application
8. Global DNS

## Practical notes by cloud

### AWS
- Use a valid AWS CLI profile before `aws-infra` and `aws-app`
- ACM / DNS / Bedrock region alignment matters
- EKS autoscaling and HPA should both be verified

### Azure
- Provider registration may take time
- OpenAI region may differ from infra region
- cert-manager and ingress timing can affect first apply
- external DNS can be managed outside Terraform if required

### GCP
- GCP ADC and active project must match
- Kubeconfig must point to the correct GKE cluster before `gcp-app`
- Existing resources from older runs may require cleanup or import

### Global DNS
- This module must be applied only after cloud endpoints are healthy
- Current failover chain is:
  1. GCP
  2. AWS
  3. Azure
- Route53 health checks need time to converge after DNS delegation changes

## Validation reminders
Before demo, verify:
- each cloud endpoint resolves correctly
- each `/health` endpoint returns `200 OK`
- TLS is valid where expected
- HPA shows CPU percentage instead of `<unknown>`
- global DNS resolves to the expected cloud based on health status
