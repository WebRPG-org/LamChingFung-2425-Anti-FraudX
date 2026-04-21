# GCP app variables

variable "project_name" {
  type    = string
  default = "anti-fraudx"
}

variable "project_id" {
  type = string
}

variable "region" {
  type    = string
  default = "asia-east2"
}

variable "db_name" {
  type    = string
  default = "antifraudx"
}

variable "db_user" {
  type    = string
  default = "antifraudx"
}

variable "db_password" {
  type      = string
  sensitive = true
}

variable "domain_name" {
  type    = string
  default = ""
}

variable "global_domain_name" {
  type    = string
  default = ""
}

variable "vertex_model" {
  type    = string
  default = "gemini-2.5-flash-lite"
}

variable "app_image" {
  type    = string
  default = "andy19982001/anti-fraudx:terraform"
}

variable "namespace" {
  type    = string
  default = "anti-fraudx-terraform"
}

variable "kubeconfig_path" {
  type    = string
  default = "~/.kube/config"
}

variable "gke_service_account_email" {
  type = string
}

variable "gke_service_account_name" {
  type = string
}

variable "cloud_sql_private_ip" {
  type = string
}

variable "dns_zone_name" {
  type    = string
  default = ""
}

variable "static_ip_name" {
  type    = string
  default = ""
}

variable "gcp_log_name" {
  type    = string
  default = "anti-fraudx-logs"
}

variable "gcp_monitoring_namespace" {
  type    = string
  default = "anti_fraudx"
}
