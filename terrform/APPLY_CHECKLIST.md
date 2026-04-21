# Terraform Apply Checklist

Use this file as the quick deployment checklist before each apply.

## 1. General checks
- Cloud credentials are valid
- `terraform.tfvars` is filled correctly
- Required quotas and APIs are ready
- Container image is already available
- DNS plan is clear before applying public ingress modules

## 2. Local Kubernetes
### Required
- Local Kubernetes cluster running
- Correct kubeconfig context
- Local image or pullable image available
- Valid values for `project_id` and `db_password`

### Apply
```bash
cd terrform/local-k8s
terraform init -upgrade
terraform plan
terraform apply -auto-approve
```

### Verify
```bash
kubectl get all -n anti-fraudx-terraform
kubectl logs deployment/anti-fraudx -n anti-fraudx-terraform
```

## 3. GCP infrastructure
### Required
- GCP login and ADC configured
- Billing enabled
- `project_id` and `db_password` set

### Apply
```bash
cd terrform/gcp-infra
terraform init -upgrade
terraform plan
terraform apply -auto-approve
```

### Verify
```bash
gcloud container clusters list --project <project_id>
gcloud sql instances list --project <project_id>
```

## 4. GCP application
### Required
- `gcp-infra` already applied
- GKE kubeconfig already fetched
- Required outputs copied into `terraform.tfvars`

### Apply
```bash
cd terrform/gcp-app
terraform init -upgrade
terraform plan
terraform apply -auto-approve
```

### Verify
```bash
kubectl get all -n anti-fraudx-terraform
kubectl get ingress -n anti-fraudx-terraform
```

## 5. AWS infrastructure
### Required
- Valid AWS credentials
- `db_password` set
- Enough quota for EKS, RDS, and networking

### Apply
```bash
cd terrform/aws-infra
terraform init -upgrade
terraform plan
terraform apply -auto-approve
```

### Verify
```bash
aws eks list-clusters --region us-east-1
```

## 6. AWS application
### Required
- `aws-infra` already applied
- EKS kubeconfig already updated
- App image available

### Apply
```bash
cd terrform/aws-app
terraform init -upgrade
terraform plan
terraform apply -auto-approve
```

### Verify
```bash
kubectl get all -n anti-fraudx-terraform
kubectl get hpa -n anti-fraudx-terraform
```

## 7. Azure infrastructure
### Required
- Valid Azure CLI login
- Correct subscription selected
- `db_password` set

### Apply
```bash
cd terrform/azure-infra
terraform init -upgrade
terraform plan
terraform apply -auto-approve
```

### Verify
```bash
az aks get-credentials --resource-group anti-fraudx-rg --name anti-fraudx-aks --overwrite-existing
kubectl get nodes
```

## 8. Azure application
### Required
- `azure-infra` already applied
- AKS kubeconfig already updated
- DNS host already planned

### Apply
```bash
cd terrform/azure-app
terraform init -upgrade
terraform plan
terraform apply -auto-approve
```

### Verify
```bash
kubectl get ingress -n anti-fraudx-terraform
kubectl get certificate -n anti-fraudx-terraform
```

## 9. Global DNS
### Required
- AWS, GCP, and Azure public endpoints already healthy
- `/health` returns `200 OK` on all endpoints
- Route53 zone and credentials are ready

### Apply
```bash
cd terrform/global-dns
terraform init -upgrade
terraform plan
terraform apply -auto-approve
```

### Verify
```bash
nslookup aws.anti-fraudx.us.ci
nslookup gcp.anti-fraudx.us.ci
nslookup azure.anti-fraudx.us.ci
nslookup app.anti-fraudx.us.ci
```
