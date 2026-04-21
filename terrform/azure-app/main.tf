terraform {
  required_version = ">= 1.6.0"
  required_providers {
    kubernetes = { source = "hashicorp/kubernetes", version = "~> 2.29" }
    helm       = { source = "hashicorp/helm", version = "~> 2.13" }
  }
}

data "terraform_remote_state" "infra" {
  backend = "local"

  config = {
    path = var.infra_state_path
  }
}

provider "kubernetes" {
  host                   = data.terraform_remote_state.infra.outputs.kube_host
  username               = data.terraform_remote_state.infra.outputs.kube_username
  password               = data.terraform_remote_state.infra.outputs.kube_password
  client_certificate     = base64decode(data.terraform_remote_state.infra.outputs.kube_client_certificate)
  client_key             = base64decode(data.terraform_remote_state.infra.outputs.kube_client_key)
  cluster_ca_certificate = base64decode(data.terraform_remote_state.infra.outputs.kube_cluster_ca_certificate)
}

provider "helm" {
  repository_config_path = "${path.module}/.helm/repositories.yaml"
  repository_cache       = "${path.module}/.helm/cache"

  kubernetes {
    host                   = data.terraform_remote_state.infra.outputs.kube_host
    username               = data.terraform_remote_state.infra.outputs.kube_username
    password               = data.terraform_remote_state.infra.outputs.kube_password
    client_certificate     = base64decode(data.terraform_remote_state.infra.outputs.kube_client_certificate)
    client_key             = base64decode(data.terraform_remote_state.infra.outputs.kube_client_key)
    cluster_ca_certificate = base64decode(data.terraform_remote_state.infra.outputs.kube_cluster_ca_certificate)
  }
}

resource "terraform_data" "preflight" {
  provisioner "local-exec" {
    interpreter = ["PowerShell", "-Command"]
    command = <<-EOT
      $ErrorActionPreference = 'Stop';
      $tools = @('az', 'kubectl', 'helm');
      foreach ($tool in $tools) {
        if (-not (Get-Command $tool -ErrorAction SilentlyContinue)) {
          throw "Missing required tool for azure-app: $tool"
        }
      }
      az account show --output none;
      $helmHome = Join-Path '${path.module}' '.helm';
      $helmCache = Join-Path $helmHome 'cache';
      $helmConfig = Join-Path $helmHome 'repositories.yaml';
      if (Test-Path $helmHome) {
        Remove-Item $helmHome -Recurse -Force -ErrorAction SilentlyContinue;
      }
      New-Item -ItemType Directory -Path $helmCache -Force | Out-Null;
      $env:HELM_REPOSITORY_CONFIG = $helmConfig;
      $env:HELM_REPOSITORY_CACHE = $helmCache;
      helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx | Out-Null;
      helm repo add jetstack https://charts.jetstack.io | Out-Null;
      helm repo update | Out-Null;
    EOT
  }
}

locals {
  namespace          = var.namespace
  azure_host         = data.terraform_remote_state.infra.outputs.azure_host
  rendered_resources = [
    for doc in split("\n---\n", replace(templatefile("${path.module}/resources.tftpl", {
      namespace  = local.namespace
      app_image  = var.app_image
      azure_host = local.azure_host
    }), "\r\n", "\n")) : yamldecode(doc) if trimspace(doc) != ""
  ]
  ingress_resource_key = one([
    for idx, manifest in local.rendered_resources : "${idx}-${manifest.kind}-${manifest.metadata.name}"
    if manifest.kind == "Ingress" && manifest.metadata.name == "anti-fraudx"
  ])
}

resource "kubernetes_namespace_v1" "app" {
  metadata {
    name = local.namespace
  }

  depends_on = [terraform_data.preflight]
}

resource "helm_release" "ingress_nginx" {
  name             = "ingress-nginx"
  repository       = "https://kubernetes.github.io/ingress-nginx"
  chart            = "ingress-nginx"
  namespace        = "ingress-nginx"
  create_namespace = true

  set {
    name  = "controller.service.externalTrafficPolicy"
    value = "Local"
  }

  depends_on = [kubernetes_namespace_v1.app]
}

resource "helm_release" "cert_manager" {
  name             = "cert-manager"
  repository       = "https://charts.jetstack.io"
  chart            = "cert-manager"
  namespace        = "cert-manager"
  create_namespace = true

  set {
    name  = "installCRDs"
    value = "true"
  }

  depends_on = [kubernetes_namespace_v1.app]
}

resource "terraform_data" "cert_manager_ready" {
  provisioner "local-exec" {
    interpreter = ["PowerShell", "-Command"]
    command = <<-EOT
      $ErrorActionPreference = 'Stop';
      kubectl wait --for=condition=established --timeout=180s crd/clusterissuers.cert-manager.io;
    EOT
  }

  depends_on = [helm_release.cert_manager]
}

resource "terraform_data" "cluster_issuer" {
  count = data.terraform_remote_state.infra.outputs.azure_host != "" ? 1 : 0

  provisioner "local-exec" {
    interpreter = ["PowerShell", "-Command"]
    command = <<-EOT
      $ErrorActionPreference = 'Stop';
      @'
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    email: ${var.letsencrypt_email}
    server: https://acme-v02.api.letsencrypt.org/directory
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
      - http01:
          ingress:
            class: nginx
'@ | kubectl apply -f -
    EOT
  }

  depends_on = [terraform_data.cert_manager_ready]
}

resource "kubernetes_secret_v1" "app_secret" {
  metadata {
    name      = "anti-fraudx-secret"
    namespace = kubernetes_namespace_v1.app.metadata[0].name
  }

  type = "Opaque"

  data = {
    AI_PROVIDER                      = "azure_openai"
    TTS_PROVIDER                     = "azure_openai"
    CLOUD_NAME                       = "azure"
    DATABASE_URL                     = "postgresql://${data.terraform_remote_state.infra.outputs.db_user}:${data.terraform_remote_state.infra.outputs.db_password}@${data.terraform_remote_state.infra.outputs.postgres_fqdn}:5432/${data.terraform_remote_state.infra.outputs.postgres_db_name}?sslmode=require"
    AZURE_OPENAI_ENDPOINT            = data.terraform_remote_state.infra.outputs.azure_openai_endpoint
    AZURE_OPENAI_DEPLOYMENT          = data.terraform_remote_state.infra.outputs.azure_openai_deployment
    AZURE_OPENAI_API_VERSION         = data.terraform_remote_state.infra.outputs.azure_openai_api_version
    AZURE_OPENAI_API_KEY             = data.terraform_remote_state.infra.outputs.azure_openai_api_key
    AZURE_SPEECH_KEY                 = data.terraform_remote_state.infra.outputs.azure_speech_key
    AZURE_SPEECH_REGION              = data.terraform_remote_state.infra.outputs.azure_speech_region
    AZURE_LOG_ANALYTICS_WORKSPACE_ID = data.terraform_remote_state.infra.outputs.log_analytics_workspace_id
    AZURE_LOG_ANALYTICS_SHARED_KEY   = data.terraform_remote_state.infra.outputs.log_analytics_shared_key
    AZURE_LOG_TYPE                   = var.azure_log_type
    AZURE_MONITOR_LOG_TYPE           = var.azure_monitor_log_type
  }
}

resource "kubernetes_config_map_v1" "scraped_alerts" {
  metadata {
    name      = "scraped-alerts"
    namespace = kubernetes_namespace_v1.app.metadata[0].name
  }

  data = {
    "scraped_alerts.json" = file("${path.module}/../../backend/data/scraped_alerts.json")
  }
}

resource "kubernetes_manifest" "app_resources" {
  for_each = {
    for idx, manifest in nonsensitive(local.rendered_resources) : "${idx}-${manifest.kind}-${manifest.metadata.name}" => manifest
  }

  manifest = each.value

  depends_on = [
    kubernetes_namespace_v1.app,
    kubernetes_secret_v1.app_secret,
    kubernetes_config_map_v1.scraped_alerts,
    helm_release.ingress_nginx,
    terraform_data.cluster_issuer[0],
  ]
}

output "namespace" { value = local.namespace }
output "dns_record_fqdn" { value = local.azure_host }
output "azure_host" { value = local.azure_host }
