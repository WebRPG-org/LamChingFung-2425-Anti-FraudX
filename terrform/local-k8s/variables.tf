variable "kubeconfig_path" {
  type    = string
  default = "~/.kube/config"
}

variable "project_id" {
  type = string
}

variable "gcp_region" {
  type    = string
  default = "asia-east2"
}

variable "gcp_location" {
  type    = string
  default = "asia-east2"
}

variable "vertex_model" {
  type    = string
  default = "gemini-2.5-flash-lite"
}

variable "vertex_service_account_id" {
  type    = string
  default = "vertex-local-runtime"
}

variable "db_password" {
  type      = string
  sensitive = true
}

variable "app_image" {
  type    = string
  default = "andy19982001/anti-fraudx:terraform"
}

variable "app_host" {
  type    = string
  default = "anti-fraudx.local"
}

variable "install_local_metrics_server" {
  type    = bool
  default = false
}
