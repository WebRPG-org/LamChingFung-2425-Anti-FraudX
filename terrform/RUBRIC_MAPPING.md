# Rubric Mapping

This document maps the project to the assignment rubric.

## 1. Using multiple cloud providers
Covered by:
- AWS deployment
- Azure deployment
- GCP deployment
- shared global DNS layer

## 2. Multiple VMs in VPC and 2 private subnets
Covered by:
- AWS VPC with public/private subnets and EKS nodes
- Azure VNet with AKS subnets and DB subnet
- GCP custom VPC with private subnet design and GKE nodes

## 3. Unique Kubernetes application with database
Covered by:
- Anti-FraudX backend
- managed PostgreSQL per cloud
- same application deployed on Kubernetes

## 4. Cluster AutoScaler
Covered by:
- node pool autoscaling in AWS, Azure, and GCP
- HPA at the application layer

## 5. Connect to database
Covered by:
- managed PostgreSQL in each cloud
- runtime database connection through environment configuration

## 6. Using Kubernetes Secret properly
Covered by:
- Kubernetes Secret for database and runtime-sensitive values
- per-cloud secret injection strategy

## 7. Using cloud-native load balancer
Covered by:
- ingress + cloud load balancer on each cloud platform

## 8. With SSL/TLS
Covered by:
- cert-manager + Let's Encrypt on cloud environments
- valid Azure TLS already verified

## 9. Stream application log data to cloud logging services
Covered by design and deployment evidence:
- AWS -> CloudWatch
- Azure -> Log Analytics / Azure Monitor
- GCP -> Cloud Logging

## 10. Multiple cloud high availability
Covered by:
- `global-dns` Route53 health checks
- failover chain GCP -> AWS -> Azure
- single public global entrypoint

## 11. Demo deployment during lab
Supported by:
- split Terraform modules
- per-cloud tfvars
- demo script and apply checklist

## 12. Individual presentation and report
Supported by:
- `REPORT_TEMPLATE.md`
- clear module ownership and cloud-specific architecture
