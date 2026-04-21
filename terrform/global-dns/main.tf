terraform {
  required_version = ">= 1.6.0"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.0" }
  }
}

provider "aws" {
  region  = var.aws_region
  profile = var.aws_profile
}

locals {
  use_existing_zone    = var.existing_route53_zone_id != ""
  zone_id              = local.use_existing_zone ? var.existing_route53_zone_id : aws_route53_zone.global[0].zone_id
  global_record_fqdn   = "${var.global_record_name}.${var.root_domain}"
  fallback_record_fqdn = "${var.fallback_record_name}.${var.root_domain}"
}

resource "aws_route53_zone" "global" {
  count = local.use_existing_zone ? 0 : 1
  name  = var.root_domain
}

resource "aws_route53_record" "aws_endpoint" {
  zone_id = local.zone_id
  name    = var.aws_endpoint
  type    = "CNAME"
  ttl     = var.record_ttl
  records = [var.aws_target]
}

resource "aws_route53_record" "gcp_endpoint" {
  zone_id = local.zone_id
  name    = var.gcp_endpoint
  type    = "A"
  ttl     = var.record_ttl
  records = [var.gcp_target]
}

resource "aws_route53_record" "azure_endpoint" {
  zone_id = local.zone_id
  name    = var.azure_endpoint
  type    = "A"
  ttl     = var.record_ttl
  records = [var.azure_target]
}

resource "aws_route53_health_check" "aws" {
  fqdn              = var.aws_endpoint
  port              = 443
  type              = "HTTPS"
  resource_path     = var.health_check_path
  request_interval  = 30
  failure_threshold = 3
  enable_sni        = true
}

resource "aws_route53_health_check" "gcp" {
  fqdn              = var.gcp_endpoint
  port              = 443
  type              = "HTTPS"
  resource_path     = var.health_check_path
  request_interval  = 30
  failure_threshold = 3
  enable_sni        = true
}

resource "aws_route53_health_check" "azure" {
  fqdn              = var.azure_endpoint
  port              = 443
  type              = "HTTPS"
  resource_path     = var.health_check_path
  request_interval  = 30
  failure_threshold = 3
  enable_sni        = true
}

resource "aws_route53_record" "fallback_primary" {
  zone_id = local.zone_id
  name    = local.fallback_record_fqdn
  type    = "CNAME"
  ttl     = var.record_ttl
  records = [var.aws_endpoint]

  set_identifier  = "fallback-aws-primary"
  health_check_id = aws_route53_health_check.aws.id

  failover_routing_policy {
    type = "PRIMARY"
  }
}

resource "aws_route53_record" "fallback_secondary" {
  zone_id = local.zone_id
  name    = local.fallback_record_fqdn
  type    = "CNAME"
  ttl     = var.record_ttl
  records = [var.azure_endpoint]

  set_identifier  = "fallback-azure-secondary"
  health_check_id = aws_route53_health_check.azure.id

  failover_routing_policy {
    type = "SECONDARY"
  }
}

resource "aws_route53_record" "global_primary" {
  zone_id = local.zone_id
  name    = local.global_record_fqdn
  type    = "CNAME"
  ttl     = var.record_ttl
  records = [var.gcp_endpoint]

  set_identifier  = "global-gcp-primary"
  health_check_id = aws_route53_health_check.gcp.id

  failover_routing_policy {
    type = "PRIMARY"
  }
}

resource "aws_route53_record" "global_secondary" {
  zone_id = local.zone_id
  name    = local.global_record_fqdn
  type    = "CNAME"
  ttl     = var.record_ttl
  records = [local.fallback_record_fqdn]

  set_identifier = "global-fallback-secondary"

  failover_routing_policy {
    type = "SECONDARY"
  }

  depends_on = [
    aws_route53_record.fallback_primary,
    aws_route53_record.fallback_secondary,
  ]
}

output "route53_zone_id" {
  value = local.zone_id
}

output "global_record_fqdn" {
  value = local.global_record_fqdn
}

output "fallback_record_fqdn" {
  value = local.fallback_record_fqdn
}

output "aws_health_check_id" {
  value = aws_route53_health_check.aws.id
}

output "gcp_health_check_id" {
  value = aws_route53_health_check.gcp.id
}

output "azure_health_check_id" {
  value = aws_route53_health_check.azure.id
}
