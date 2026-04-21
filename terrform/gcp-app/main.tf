terraform {
  required_version = ">= 1.6.0"
  required_providers {
    google = { source = "hashicorp/google", version = "~> 5.30" }
    kubernetes = { source = "hashicorp/kubernetes", version = "~> 2.29" }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

provider "kubernetes" {
  config_path = var.kubeconfig_path
}

resource "terraform_data" "preflight" {
  provisioner "local-exec" {
    interpreter = ["PowerShell", "-Command"]
    command = <<-EOT
      $ErrorActionPreference = 'Stop';
      $tools = @('kubectl', 'gcloud');
      foreach ($tool in $tools) {
        if (-not (Get-Command $tool -ErrorAction SilentlyContinue)) {
          throw "Missing required tool for gcp-app: $tool"
        }
      }
      $ctx = kubectl config current-context;
      if (-not $ctx.StartsWith('gke_')) {
        throw "gcp-app requires an active GKE kubectl context. Current context: $ctx"
      }
      kubectl get crd managedcertificates.networking.gke.io | Out-Null;
      gcloud auth list --filter=status:ACTIVE --format="value(account)" | Out-Null;
    EOT
  }
}

resource "google_compute_global_address" "gcp_ingress_ip" {
  name = var.static_ip_name != "" ? var.static_ip_name : "${var.project_name}-gcp-app-ip"
}

locals {
  namespace   = var.namespace
  gcp_host    = var.domain_name != "" ? var.domain_name : "${var.project_name}.local"
  global_host = var.global_domain_name

  managed_certificate_domains = compact([
    local.gcp_host,
    local.global_host,
  ])

  ingress_hosts = compact([
    local.gcp_host,
    local.global_host,
  ])

  rendered_resources = [
    for doc in split("\n---\n", replace(templatefile("${path.module}/resources.tftpl", {
      namespace                   = local.namespace
      gcp_service_account_email   = var.gke_service_account_email
      app_image                   = var.app_image
      managed_certificate_domains = local.managed_certificate_domains
      ingress_hosts               = local.ingress_hosts
      static_ip_name              = google_compute_global_address.gcp_ingress_ip.name
    }), "\r\n", "\n")) : yamldecode(doc) if trimspace(doc) != ""
  ]

  rendered_resources_by_key = {
    serviceaccount     = local.rendered_resources[0]
    managedcertificate = local.rendered_resources[1]
    deployment         = local.rendered_resources[2]
    service            = local.rendered_resources[3]
    ingress            = local.rendered_resources[4]
    hpa                = local.rendered_resources[5]
  }
}

resource "google_service_account_iam_member" "workload_identity" {
  service_account_id = var.gke_service_account_name
  role               = "roles/iam.workloadIdentityUser"
  member             = "serviceAccount:${var.project_id}.svc.id.goog[${local.namespace}/anti-fraudx-app]"

  depends_on = [terraform_data.preflight]
}

resource "kubernetes_namespace_v1" "app" {
  metadata {
    name = local.namespace
  }
}

resource "kubernetes_secret_v1" "app_secret" {
  metadata {
    name      = "anti-fraudx-secret"
    namespace = kubernetes_namespace_v1.app.metadata[0].name
  }

  type = "Opaque"

  data = {
    AI_PROVIDER              = "vertex"
    CLOUD_NAME               = "gcp"
    DATABASE_URL             = "postgresql://${var.db_user}:${var.db_password}@${var.cloud_sql_private_ip}:5432/${var.db_name}"
    GCP_PROJECT_ID           = var.project_id
    GCP_LOCATION             = var.region
    VERTEX_AI_MODEL          = var.vertex_model
    GCP_LOG_NAME             = var.gcp_log_name
    GCP_MONITORING_NAMESPACE = var.gcp_monitoring_namespace
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
  for_each = toset([
    "serviceaccount",
    "managedcertificate",
    "deployment",
    "service",
    "ingress",
    "hpa",
  ])

  manifest = local.rendered_resources_by_key[each.key]

  depends_on = [
    kubernetes_namespace_v1.app,
    kubernetes_secret_v1.app_secret,
    kubernetes_config_map_v1.scraped_alerts,
    google_service_account_iam_member.workload_identity,
    google_compute_global_address.gcp_ingress_ip,
  ]
}

resource "google_dns_record_set" "app" {
  count = var.domain_name != "" && var.dns_zone_name != "" ? 1 : 0

  managed_zone = var.dns_zone_name
  name         = "${var.domain_name}."
  type         = "A"
  ttl          = 300
  rrdatas      = [google_compute_global_address.gcp_ingress_ip.address]

  depends_on = [
    google_compute_global_address.gcp_ingress_ip,
    kubernetes_manifest.app_resources,
  ]
}

output "namespace" { value = local.namespace }
output "dns_record_name" { value = try(google_dns_record_set.app[0].name, "") }
output "gcp_host" { value = local.gcp_host }
output "static_ip_name" { value = google_compute_global_address.gcp_ingress_ip.name }
output "static_ip_address" { value = google_compute_global_address.gcp_ingress_ip.address }
