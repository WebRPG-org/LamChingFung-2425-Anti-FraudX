variable "infra_state_path" {
  type    = string
  default = "../azure-infra/terraform.tfstate"
}

variable "namespace" {
  type    = string
  default = "anti-fraudx-terraform"
}

variable "letsencrypt_email" {
  type = string
}

variable "azure_log_type" {
  type    = string
  default = "AntiFraudXLogs"
}

variable "azure_monitor_log_type" {
  type    = string
  default = "AntiFraudXMetrics"
}

variable "app_image" {
  type    = string
  default = "andy19982001/anti-fraudx:terraform"
}
