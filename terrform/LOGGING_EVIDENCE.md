# Logging Evidence

This document explains how logging is handled across the Terraform environments.

## Logging model
The application writes logs to stdout/stderr. Each cloud environment then forwards container logs into its own native logging platform.

## AWS
- Platform: CloudWatch
- Source: EKS workloads
- Demo evidence:
  - `kubectl logs deployment/anti-fraudx -n anti-fraudx-terraform`
  - CloudWatch log groups / Container Insights if enabled

## Azure
- Platform: Azure Monitor / Log Analytics
- Source: AKS workloads and diagnostics
- Demo evidence:
  - `kubectl logs deployment/anti-fraudx -n anti-fraudx-terraform`
  - Log Analytics Workspace and AKS diagnostics

## GCP
- Platform: Cloud Logging
- Source: GKE workloads
- Demo evidence:
  - `kubectl logs deployment/anti-fraudx -n anti-fraudx-terraform`
  - GCP Logs Explorer filters for namespace and workload

## What to say during demo
- The application uses the same logging style in every environment
- Each cloud collects those logs using its native logging stack
- This satisfies the cloud logging requirement without changing app code per cloud

## Strongest evidence
Best evidence includes:
- working pod logs from Kubernetes
- screenshot or live view in cloud logging console
- one API call followed by visible logs in the target cloud logging service
