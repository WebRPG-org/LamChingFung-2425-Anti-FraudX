variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "aws_profile" {
  type    = string
  default = "terraform-deployer"
}

variable "root_domain" {
  type = string
}

variable "global_record_name" {
  type    = string
  default = "app"
}

variable "fallback_record_name" {
  type    = string
  default = "fallback-app"
}

variable "existing_route53_zone_id" {
  type    = string
  default = ""
}

variable "aws_endpoint" {
  type = string
}

variable "aws_target" {
  type = string
}

variable "gcp_endpoint" {
  type = string
}

variable "gcp_target" {
  type = string
}

variable "azure_endpoint" {
  type = string
}

variable "azure_target" {
  type = string
}

variable "health_check_path" {
  type    = string
  default = "/health"
}

variable "record_ttl" {
  type    = number
  default = 60
}
