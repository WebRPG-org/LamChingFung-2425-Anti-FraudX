# Demo Script and Full Verification Flow

This document is the full demo runbook for the Terraform-based `Anti-FraudX` multi-cloud deployment.
It is written for a live lab demonstration and focuses on showing working evidence instead of theory only.

## Demo goal
The demo should prove the following:
- multiple cloud providers are used
- each cloud runs a Kubernetes-based deployment
- private networking and multiple worker nodes exist
- the application connects to a database
- Kubernetes Secret is used properly
- cloud-native load balancers are in use
- TLS / HTTPS works
- autoscaling works
- cloud logging is wired by platform design
- global DNS failover works

## Current project structure
- `terrform/aws-infra`
- `terrform/aws-app`
- `terrform/azure-infra`
- `terrform/azure-app`
- `terrform/gcp-infra`
- `terrform/gcp-app`
- `terrform/global-dns`
- `terrform/local-k8s`

## Recommended live demo strategy
For a short live demo, do not redeploy every cloud from scratch.
The safest approach is:
1. show the deployed cloud endpoints are healthy
2. show Kubernetes / autoscaling / TLS evidence
3. show database / secret / load balancer evidence
4. show global DNS failover
5. explain logging and architecture mapping to the rubric

---

# 1. Pre-demo checklist

Run or verify these before the demo starts.

## 1.1 DNS and health endpoints
Check that all cloud endpoints are reachable:

```powershell
curl.exe "https://aws.anti-fraudx.us.ci/health"
curl.exe "https://gcp.anti-fraudx.us.ci/health"
curl.exe "https://azure.anti-fraudx.us.ci/health"
```

Expected pattern:
- AWS returns `cloud: aws`
- GCP returns `cloud: gcp`
- Azure returns `cloud: azure`

## 1.2 Global DNS
Check the global records:

```powershell
nslookup aws.anti-fraudx.us.ci
nslookup gcp.anti-fraudx.us.ci
nslookup azure.anti-fraudx.us.ci
nslookup fallback-app.anti-fraudx.us.ci
nslookup app.anti-fraudx.us.ci
```

## 1.3 AWS credentials for global DNS proof
```powershell
$env:AWS_PROFILE="terraform-deployer"
aws sts get-caller-identity
```

## 1.4 Azure AKS context ready
```powershell
az aks get-credentials --resource-group anti-fraudx-rg --name anti-fraudx-aks --overwrite-existing
kubectl get nodes
```

## 1.5 Optional checks before the room starts
```powershell
kubectl get pods -n anti-fraudx-terraform
kubectl get hpa -n anti-fraudx-terraform
kubectl get certificate -n anti-fraudx-terraform
```

---

# 2. Opening script

Suggested opening:

> Our project is Anti-FraudX, a multi-cloud Kubernetes deployment built with Terraform. We deployed the same backend architecture across AWS, Azure, and GCP, with managed databases, Kubernetes Secrets, autoscaling, HTTPS, and a global Route53 failover layer.

---

# 3. Show the repository structure

Open the `terrform/` folder and explain:
- `aws-infra` and `aws-app` split infrastructure and app on AWS
- `azure-infra` and `azure-app` split infrastructure and app on Azure
- `gcp-infra` and `gcp-app` split infrastructure and app on GCP
- `global-dns` is the final DNS failover layer
- `local-k8s` is used for development and fallback verification

Suggested sentence:

> We separated infrastructure and application layers per cloud so that provisioning, debugging, and redeployment are easier and safer.

---

# 4. Prove multiple cloud providers are deployed

## 4.1 Show health endpoint from each cloud

```powershell
curl.exe "https://aws.anti-fraudx.us.ci/health"
curl.exe "https://gcp.anti-fraudx.us.ci/health"
curl.exe "https://azure.anti-fraudx.us.ci/health"
```

What to say:
- AWS uses Bedrock
- GCP uses Vertex AI
- Azure uses Azure OpenAI
- same backend concept, different cloud-native AI integration

This directly supports:
- Using multiple Cloud Providers
- Unique Kubernetes Application with database

---

# 5. Prove Kubernetes cluster, nodes, and networking

## 5.1 Azure AKS nodes

```powershell
kubectl get nodes
```

Expected evidence:
- more than one node
- separate worker nodes exist

## 5.2 Explain private networking
For live explanation, say:
- AWS VPC has public and private subnets
- Azure VNet has AKS subnets and DB subnet
- GCP VPC has subnet design for GKE and Cloud SQL

This supports:
- Multiple VMs in VPC and 2 private subnets

---

# 6. Prove the application is running on Kubernetes

## 6.1 Azure app namespace

```powershell
kubectl get pods -n anti-fraudx-terraform
kubectl get svc -n anti-fraudx-terraform
kubectl get ingress -n anti-fraudx-terraform
```

What to point out:
- deployment is running
- service exists
- ingress is exposed publicly
- ingress address matches the DNS target

This supports:
- Unique Kubernetes Application with database
- Using cloud native load balancer

---

# 7. Prove Kubernetes Secret usage

## 7.1 Show Secret exists

```powershell
kubectl get secret -n anti-fraudx-terraform
```

## 7.2 Show deployment references the Secret without printing secret values

```powershell
kubectl get deployment anti-fraudx -n anti-fraudx-terraform -o yaml
```

What to point out in the output:
- `envFrom`
- `secretRef`
- name such as `anti-fraudx-secret`

Do not print secret contents live unless absolutely required.

This supports:
- Using Kubernetes Secret properly

---

# 8. Prove database connectivity

## 8.1 Use health endpoint and app behavior as live evidence

```powershell
curl.exe "https://azure.anti-fraudx.us.ci/health"
```

## 8.2 Show deployment carries a database connection path

```powershell
kubectl get deployment anti-fraudx -n anti-fraudx-terraform -o yaml
```

What to say:
- the backend uses `DATABASE_URL`
- each cloud points to its own managed PostgreSQL service
- AWS uses RDS
- Azure uses Azure Database for PostgreSQL
- GCP uses Cloud SQL

This supports:
- Connect to Database
- Unique Kubernetes Application with database

---

# 9. Prove TLS / HTTPS works

## 9.1 DNS already resolves

```powershell
nslookup azure.anti-fraudx.us.ci
```

## 9.2 cert-manager evidence on Azure

```powershell
kubectl get certificate -n anti-fraudx-terraform
kubectl get order -A
kubectl get challenge -A
```

Expected evidence:
- certificate `READY=True`
- order `valid`
- no pending challenge

## 9.3 Live HTTPS test

```powershell
curl.exe "https://azure.anti-fraudx.us.ci/health"
```

This supports:
- With SSL/TLS

---

# 10. Prove HPA and autoscaling configuration

## 10.1 Show HPA exists

```powershell
kubectl get hpa -n anti-fraudx-terraform
kubectl describe hpa anti-fraudx -n anti-fraudx-terraform
```

Expected evidence:
- CPU target is shown as a percentage
- HPA conditions include `ScalingActive=True`

## 10.2 Show deployment has CPU requests and limits

```powershell
kubectl get deployment anti-fraudx -n anti-fraudx-terraform -o yaml
```

Point out:
- `resources.requests.cpu`
- `resources.limits.cpu`

This supports:
- Cluster AutoScaler
- App-level autoscaling evidence

---

# 11. Live stress test to show HPA reacts

Use PowerShell jobs to generate concurrent load against the public endpoint.

## 11.1 Start HPA watch in one terminal

```powershell
kubectl get hpa -n anti-fraudx-terraform -w
```

## 11.2 Run stress traffic in another terminal

This generates parallel GET requests to the public health endpoint.

```powershell
1..8 | ForEach-Object {
  Start-Job -ScriptBlock {
    1..200 | ForEach-Object {
      try {
        Invoke-WebRequest -Uri "https://azure.anti-fraudx.us.ci/health" -Method Get | Out-Null
      } catch {
      }
    }
  }
}
```

## 11.3 Monitor jobs

```powershell
Get-Job
```

## 11.4 Clean up jobs after the test

```powershell
Get-Job | Stop-Job -ErrorAction SilentlyContinue
Get-Job | Remove-Job -Force -ErrorAction SilentlyContinue
```

What to say:
- HPA reads CPU usage and compares it to target utilization
- if the average load rises high enough, replicas should increase
- even if scaling does not happen immediately during a short demo, the HPA object and valid metrics already prove correct autoscaling configuration

---

# 12. Prove cloud-native load balancer

## 12.1 Show ingress address

```powershell
kubectl get ingress -n anti-fraudx-terraform
```

Point out:
- public address exists
- DNS points to it
- the cloud is providing the public ingress / load balancer path

This supports:
- Using Cloud native load balancer

---

# 13. Prove global multi-cloud failover

## 13.1 Show the cloud-specific records

```powershell
nslookup aws.anti-fraudx.us.ci
nslookup gcp.anti-fraudx.us.ci
nslookup azure.anti-fraudx.us.ci
```

## 13.2 Show the global records

```powershell
nslookup fallback-app.anti-fraudx.us.ci
nslookup app.anti-fraudx.us.ci
```

Explain the failover chain:
1. GCP primary
2. AWS secondary
3. Azure tertiary

## 13.3 Show AWS health check status in Route53

```powershell
aws route53 get-health-check-status --health-check-id efbc59cb-ca84-4679-b705-4b40fe1dad46 --profile terraform-deployer
```

What to say:
- Route53 checks `/health`
- if GCP is unhealthy, traffic shifts to AWS
- if AWS is also unhealthy, traffic can fall through to Azure
- DNS failover is health-check driven, so propagation and recovery are not instant

## 13.4 Optional failover explanation
If `app.anti-fraudx.us.ci` currently resolves to AWS while GCP is recovering, explain:
- health checks are converging
- Route53 uses observed health rather than manual priority only
- this is expected behavior during DNS propagation or health recovery

This supports:
- Multiple Cloud High Availability
- Using multiple Cloud Providers

---

# 14. Logging evidence talking points

If you do not have time to open every cloud console, explain clearly:
- AWS logs are collected through CloudWatch
- Azure logs are collected through Azure Monitor / Log Analytics
- GCP logs are collected through Cloud Logging
- the app always logs to stdout/stderr, so the application code stays the same while each cloud uses its native logging system

If you want one live Kubernetes-side proof:

```powershell
kubectl logs deployment/anti-fraudx -n anti-fraudx-terraform
```

This supports:
- Stream application log data to cloud logging services

---

# 15. Fast rubric-to-command mapping

## Using multiple Cloud Providers
```powershell
curl.exe "https://aws.anti-fraudx.us.ci/health"
curl.exe "https://gcp.anti-fraudx.us.ci/health"
curl.exe "https://azure.anti-fraudx.us.ci/health"
```

## Multiple VMs in VPC and 2 private subnets
```powershell
kubectl get nodes
```
Plus architecture explanation from Terraform modules.

## Unique Kubernetes Application with database
```powershell
kubectl get pods -n anti-fraudx-terraform
curl.exe "https://azure.anti-fraudx.us.ci/health"
```

## Cluster AutoScaler
```powershell
kubectl get hpa -n anti-fraudx-terraform
kubectl describe hpa anti-fraudx -n anti-fraudx-terraform
```

## Connect to Database
```powershell
kubectl get deployment anti-fraudx -n anti-fraudx-terraform -o yaml
```
Then explain `DATABASE_URL` and managed PostgreSQL.

## Using Kubernetes Secret properly
```powershell
kubectl get secret -n anti-fraudx-terraform
kubectl get deployment anti-fraudx -n anti-fraudx-terraform -o yaml
```

## Using Cloud native load balancer
```powershell
kubectl get ingress -n anti-fraudx-terraform
```

## With SSL/TLS
```powershell
kubectl get certificate -n anti-fraudx-terraform
kubectl get order -A
curl.exe "https://azure.anti-fraudx.us.ci/health"
```

## Stream application log data to cloud logging services
```powershell
kubectl logs deployment/anti-fraudx -n anti-fraudx-terraform
```
Then explain cloud-native log platforms.

## Multiple Cloud High Availability
```powershell
nslookup app.anti-fraudx.us.ci
aws route53 get-health-check-status --health-check-id efbc59cb-ca84-4679-b705-4b40fe1dad46 --profile terraform-deployer
```

---

# 16. Suggested closing statement

> This project demonstrates a complete multi-cloud Terraform workflow with Kubernetes application deployment, managed databases, Secret-based runtime configuration, autoscaling, HTTPS, cloud-native logging, and Route53-based global failover across AWS, GCP, and Azure.
