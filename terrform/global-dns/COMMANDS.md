# Global DNS Commands

## Purpose
Deploy the final Route53 global DNS failover layer.

## Routing order
The current failover chain is:
1. GCP
2. AWS
3. Azure

## Before apply
- AWS, GCP, and Azure endpoints already exist
- all three endpoints return `200 OK` on `/health`
- Route53 credentials are valid
- DNS delegation plan is already prepared

## Commands
```bash
cd terrform/global-dns
terraform init -upgrade
terraform plan
terraform apply -auto-approve
```

## Verify
```bash
nslookup aws.anti-fraudx.us.ci
nslookup gcp.anti-fraudx.us.ci
nslookup azure.anti-fraudx.us.ci
nslookup app.anti-fraudx.us.ci
```

## Notes
- apply this module last
- Route53 health checks need time to converge after DNS or delegation changes
- if GCP is unhealthy, `app.anti-fraudx.us.ci` should fail over to AWS
