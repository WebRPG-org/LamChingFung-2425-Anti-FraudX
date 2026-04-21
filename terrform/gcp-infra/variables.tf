# GCP infra variables

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

variable "zone" {
  type    = string
  default = "asia-east2-a"
}

variable "machine_type" {
  type    = string
  default = "e2-standard-2"
}

variable "db_tier" {
  type    = string
  default = "db-custom-1-3840"
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
