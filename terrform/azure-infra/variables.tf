variable "project_name" {
  type    = string
  default = "anti-fraudx"
}

variable "location" {
  type    = string
  default = "centralus"
}

variable "vnet_cidr" {
  type    = string
  default = "10.20.0.0/16"
}

variable "aks_subnet_a_cidr" {
  type    = string
  default = "10.20.1.0/24"
}

variable "aks_subnet_b_cidr" {
  type    = string
  default = "10.20.2.0/24"
}

variable "db_subnet_cidr" {
  type    = string
  default = "10.20.3.0/24"
}

variable "node_vm_size" {
  type    = string
  default = "Standard_D2s_v3"
}

variable "db_sku_name" {
  type    = string
  default = "B_Standard_B1ms"
}

variable "db_name" {
  type    = string
  default = "antifraudx"
}

variable "db_user" {
  type    = string
  default = "antifraudxadmin"
}

variable "db_password" {
  type      = string
  sensitive = true
}

variable "domain_name" {
  type    = string
  default = ""
}

variable "azure_openai_deployment" {
  type    = string
  default = "gpt-4.1-mini"
}

variable "azure_openai_api_version" {
  type    = string
  default = "2024-02-15-preview"
}

variable "azure_openai_region" {
  type    = string
  default = "eastus"
}

variable "azure_openai_model_name" {
  type    = string
  default = "gpt-4.1-mini"
}

variable "azure_openai_model_version" {
  type    = string
  default = "2025-04-14"
}

variable "azure_speech_region" {
  type    = string
  default = "centralus"
}
