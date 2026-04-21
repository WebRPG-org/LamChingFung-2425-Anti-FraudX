terraform {
  required_version = ">= 1.6.0"
  required_providers {
    google = { source = "hashicorp/google", version = "~> 5.30" }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

resource "terraform_data" "preflight" {
  provisioner "local-exec" {
    interpreter = ["PowerShell", "-Command"]
    command = <<-EOT
      $ErrorActionPreference = 'Stop';
      if (-not (Get-Command gcloud -ErrorAction SilentlyContinue)) {
        throw 'Missing required tool for gcp-infra: gcloud'
      }
      $acct = gcloud auth list --filter=status:ACTIVE --format="value(account)";
      if (-not $acct) {
        throw 'No active gcloud account found. Run gcloud auth login first.'
      }
      gcloud config get-value project | Out-Null;
    EOT
  }
}

resource "google_project_service" "compute" {
  project            = var.project_id
  service            = "compute.googleapis.com"
  disable_on_destroy = false

  depends_on = [terraform_data.preflight]
}

resource "google_project_service" "container" {
  project            = var.project_id
  service            = "container.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "sqladmin" {
  project            = var.project_id
  service            = "sqladmin.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "servicenetworking" {
  project            = var.project_id
  service            = "servicenetworking.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "dns" {
  project            = var.project_id
  service            = "dns.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "aiplatform" {
  project            = var.project_id
  service            = "aiplatform.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "iamcredentials" {
  project            = var.project_id
  service            = "iamcredentials.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "texttospeech" {
  project            = var.project_id
  service            = "texttospeech.googleapis.com"
  disable_on_destroy = false
}

resource "google_compute_network" "vpc" {
  name                    = "${var.project_name}-vpc"
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "private_a" {
  name                     = "private-a"
  ip_cidr_range            = "10.30.1.0/24"
  region                   = var.region
  network                  = google_compute_network.vpc.id
  private_ip_google_access = true

  secondary_ip_range {
    range_name    = "gke-pods"
    ip_cidr_range = "10.40.0.0/16"
  }

  secondary_ip_range {
    range_name    = "gke-services"
    ip_cidr_range = "10.50.0.0/20"
  }
}

resource "google_compute_subnetwork" "private_b" {
  name                     = "private-b"
  ip_cidr_range            = "10.30.2.0/24"
  region                   = var.region
  network                  = google_compute_network.vpc.id
  private_ip_google_access = true
}

resource "google_compute_global_address" "private_ip_alloc" {
  name          = "${var.project_name}-private-ip-alloc"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.vpc.id

  depends_on = [google_project_service.servicenetworking]
}

resource "google_service_networking_connection" "private_vpc_connection" {
  network                 = google_compute_network.vpc.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip_alloc.name]

  depends_on = [google_compute_global_address.private_ip_alloc]
}

resource "google_service_account" "gke_vertex" {
  account_id   = "${var.project_name}-gke-vertex"
  display_name = "GKE Vertex AI service account"
}

resource "google_project_iam_member" "vertex_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.gke_vertex.email}"
}

resource "google_project_iam_member" "log_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.gke_vertex.email}"
}

resource "google_project_iam_member" "metric_writer" {
  project = var.project_id
  role    = "roles/monitoring.metricWriter"
  member  = "serviceAccount:${google_service_account.gke_vertex.email}"
}

resource "google_container_cluster" "gke" {
  name     = "${var.project_name}-gke"
  location = var.zone

  network    = google_compute_network.vpc.id
  subnetwork = google_compute_subnetwork.private_a.id

  remove_default_node_pool = true
  initial_node_count       = 1

  ip_allocation_policy {
    cluster_secondary_range_name  = "gke-pods"
    services_secondary_range_name = "gke-services"
  }

  workload_identity_config {
    workload_pool = "${var.project_id}.svc.id.goog"
  }

  logging_service    = "logging.googleapis.com/kubernetes"
  monitoring_service = "monitoring.googleapis.com/kubernetes"

  depends_on = [
    google_project_service.compute,
    google_project_service.container,
    google_project_service.aiplatform,
    google_project_service.iamcredentials,
  ]
}

resource "google_container_node_pool" "primary" {
  name       = "primary"
  location   = var.zone
  cluster    = google_container_cluster.gke.name
  node_count = 2

  autoscaling {
    min_node_count = 2
    max_node_count = 5
  }

  node_config {
    machine_type    = var.machine_type
    service_account = google_service_account.gke_vertex.email
    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]
  }
}

resource "google_sql_database_instance" "postgres" {
  name             = "${var.project_name}-postgres"
  database_version = "POSTGRES_15"
  region           = var.region

  settings {
    tier              = var.db_tier
    availability_type = "ZONAL"

    ip_configuration {
      ipv4_enabled    = false
      private_network = google_compute_network.vpc.id
    }

    backup_configuration {
      enabled = true
    }
  }

  deletion_protection = false

  depends_on = [
    google_project_service.sqladmin,
    google_service_networking_connection.private_vpc_connection,
  ]
}

resource "google_sql_database" "app" {
  name     = var.db_name
  instance = google_sql_database_instance.postgres.name
}

resource "google_sql_user" "app" {
  name     = var.db_user
  instance = google_sql_database_instance.postgres.name
  password = var.db_password
}

resource "google_dns_managed_zone" "anti_fraudx" {
  count       = var.domain_name != "" ? 1 : 0
  name        = replace("${var.project_name}-zone", "_", "-")
  dns_name    = "${trimsuffix(var.domain_name, ".")}."
  description = "Cloud DNS zone for Anti-FraudX"

  depends_on = [google_project_service.dns]
}

locals {
  gcp_host = var.domain_name != "" ? var.domain_name : "${var.project_name}.local"
}

output "cluster_name" { value = google_container_cluster.gke.name }
output "cluster_location" { value = var.zone }
output "cluster_endpoint" { value = google_container_cluster.gke.endpoint }
output "gke_service_account_email" { value = google_service_account.gke_vertex.email }
output "gke_service_account_name" { value = google_service_account.gke_vertex.name }
output "cloud_sql_private_ip" { value = google_sql_database_instance.postgres.private_ip_address }
output "database_name" { value = google_sql_database.app.name }
output "database_user" { value = google_sql_user.app.name }
output "dns_zone_name" { value = var.domain_name != "" ? google_dns_managed_zone.anti_fraudx[0].name : "" }
output "gcp_host" { value = local.gcp_host }
