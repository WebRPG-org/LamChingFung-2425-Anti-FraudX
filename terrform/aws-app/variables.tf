variable "project_name" {
  type    = string
  default = "anti-fraudx"
}

variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "db_name" {
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

variable "bedrock_model_id" {
  type    = string
  default = "amazon.nova-lite-v1:0"
}

variable "aws_load_balancer_scheme" {
  type    = string
  default = "internet-facing"
}

variable "aws_acm_certificate_arn" {
  type    = string
  default = ""
}

variable "app_image" {
  type    = string
  default = "andy19982001/anti-fraudx:terraform"
}

variable "aws_log_group_name" {
  type    = string
  default = "/anti-fraudx/custom/application"
}

variable "aws_log_stream_name" {
  type    = string
  default = "anti-fraudx-app"
}

variable "aws_monitoring_namespace" {
  type    = string
  default = "AntiFraudX"
}

variable "aws_polly_engine" {
  type    = string
  default = "neural"
}
