variable "project_name" {
  type    = string
  default = "anti-fraudx"
}

variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "kubernetes_version" {
  type    = string
  default = "1.29"
}

variable "vpc_cidr" {
  type    = string
  default = "10.10.0.0/16"
}

variable "private_subnets" {
  type    = list(string)
  default = ["10.10.1.0/24", "10.10.2.0/24"]
}

variable "public_subnets" {
  type    = list(string)
  default = ["10.10.101.0/24", "10.10.102.0/24"]
}

variable "node_instance_type" {
  type    = string
  default = "t3.medium"
}

variable "db_instance_class" {
  type    = string
  default = "db.t3.micro"
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

variable "eks_log_retention_days" {
  type    = number
  default = 30
}

variable "app_log_retention_days" {
  type    = number
  default = 30
}
