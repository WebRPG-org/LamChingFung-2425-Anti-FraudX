# Shared Kubernetes Assets

This folder contains shared Kubernetes support files used across environments.

## Typical contents
- cluster issuer definitions
- certificate templates
- shared ingress / TLS support files

## Typical use order
1. install ingress controller
2. install cert-manager
3. apply issuer
4. deploy application manifests
5. verify ingress, certificate, and pods
