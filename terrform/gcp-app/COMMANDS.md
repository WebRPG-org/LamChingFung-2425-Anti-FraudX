# GCP Application Commands

## Purpose
Deploy the Kubernetes application layer on the GKE cluster created by `gcp-infra`.

## Before apply
- `gcp-infra` already applied
- kubeconfig already points to the target GKE cluster
- required outputs from `gcp-infra` have been copied into `terraform.tfvars`

## Prepare kubeconfig
```bash
gcloud container clusters get-credentials <cluster_name> --zone <cluster_location> --project <project_id>
kubectl get nodes
```

## Commands
```bash
cd terrform/gcp-app
terraform init -upgrade
terraform plan
terraform apply -auto-approve
```

## Verify
```bash
kubectl get all -n anti-fraudx-terraform
kubectl get ingress -n anti-fraudx-terraform
kubectl logs deployment/anti-fraudx -n anti-fraudx-terraform
```
