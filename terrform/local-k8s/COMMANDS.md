# Local Kubernetes Commands

## Purpose
Deploy the application locally for development, validation, and fallback testing.

## Before apply
- local Kubernetes cluster is running
- kubeconfig points to the correct local context
- local or pullable image is available
- `terraform.tfvars` is ready

## Commands
```bash
cd terrform/local-k8s
terraform init -upgrade
terraform plan
terraform apply -auto-approve
```

## Verify
```bash
kubectl get all -n anti-fraudx-terraform
kubectl logs deployment/anti-fraudx -n anti-fraudx-terraform
kubectl get ingress -n anti-fraudx-terraform
```
