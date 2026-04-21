terraform {
  required_version = ">= 1.6.0"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.0" }
    kubernetes = { source = "hashicorp/kubernetes", version = "~> 2.29" }
  }
}

provider "aws" {
  region  = var.aws_region
  profile = "terraform-deployer"
}

data "terraform_remote_state" "infra" {
  backend = "local"

  config = {
    path = "../aws-infra/terraform.tfstate"
  }
}

data "aws_eks_cluster" "cluster" {
  name = data.terraform_remote_state.infra.outputs.cluster_name
}

data "aws_eks_cluster_auth" "cluster" {
  name = data.terraform_remote_state.infra.outputs.cluster_name
}

resource "terraform_data" "update_kubeconfig" {
  provisioner "local-exec" {
    interpreter = ["PowerShell", "-Command"]
    command     = "aws eks update-kubeconfig --name ${data.terraform_remote_state.infra.outputs.cluster_name} --region ${var.aws_region} --profile terraform-deployer 2>$null"
  }

  depends_on = [data.aws_eks_cluster.cluster]
}

resource "terraform_data" "install_metrics_server" {
  depends_on = [terraform_data.update_kubeconfig]

  provisioner "local-exec" {
    interpreter = ["PowerShell", "-Command"]
    command     = "kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml 2>$null"
  }
}

provider "kubernetes" {
  host                   = data.aws_eks_cluster.cluster.endpoint
  cluster_ca_certificate = base64decode(data.aws_eks_cluster.cluster.certificate_authority[0].data)
  token                  = data.aws_eks_cluster_auth.cluster.token
}

locals {
  namespace = "anti-fraudx-terraform"
  aws_host  = var.domain_name != "" ? var.domain_name : data.terraform_remote_state.infra.outputs.aws_host
  effective_acm_certificate_arn = var.aws_acm_certificate_arn != "" ? var.aws_acm_certificate_arn : try(aws_acm_certificate_validation.app[0].certificate_arn, "")
  rendered_resources = [
    for doc in split("\n---\n", replace(templatefile("${path.module}/resources.tftpl", {
      namespace               = local.namespace
      role_arn                = data.terraform_remote_state.infra.outputs.app_role_arn
      autoscaler_role_arn     = data.terraform_remote_state.infra.outputs.cluster_autoscaler_role_arn
      db_password             = var.db_password
      rds_endpoint            = data.terraform_remote_state.infra.outputs.rds_endpoint
      aws_region              = var.aws_region
      cluster_name            = data.terraform_remote_state.infra.outputs.cluster_name
      bedrock_model_id        = var.bedrock_model_id
      app_image               = var.app_image
      aws_host                = local.aws_host
      aws_lb_name             = "${var.project_name}-anti-fraudx-nlb"
      aws_lb_scheme           = var.aws_load_balancer_scheme
      aws_acm_certificate_arn = local.effective_acm_certificate_arn
    }), "\r\n", "\n")) : yamldecode(doc) if trimspace(doc) != ""
  ]
}

resource "aws_acm_certificate" "app" {
  count             = var.domain_name != "" && var.aws_acm_certificate_arn == "" ? 1 : 0
  domain_name       = var.domain_name
  validation_method = "DNS"

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_route53_record" "app_cert_validation" {
  for_each = var.domain_name != "" && var.aws_acm_certificate_arn == "" ? {
    for dvo in aws_acm_certificate.app[0].domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  } : {}

  zone_id = data.terraform_remote_state.infra.outputs.route53_zone_id
  name    = each.value.name
  type    = each.value.type
  ttl     = 60
  records = [each.value.record]
}

resource "aws_acm_certificate_validation" "app" {
  count                   = var.domain_name != "" && var.aws_acm_certificate_arn == "" ? 1 : 0
  certificate_arn         = aws_acm_certificate.app[0].arn
  validation_record_fqdns = [for record in aws_route53_record.app_cert_validation : record.fqdn]
}

resource "kubernetes_namespace_v1" "app" {
  metadata {
    name = local.namespace
  }
}

resource "kubernetes_secret_v1" "app_secret" {
  metadata {
    name      = "anti-fraudx-secret"
    namespace = kubernetes_namespace_v1.app.metadata[0].name
  }

  type = "Opaque"

  data = {
    AI_PROVIDER              = "bedrock"
    TTS_PROVIDER             = "bedrock"
    CLOUD_NAME               = "aws"
    DATABASE_URL             = "postgresql://antifraudx:${var.db_password}@${data.terraform_remote_state.infra.outputs.rds_endpoint}:5432/${var.db_name}"
    AWS_REGION               = var.aws_region
    BEDROCK_MODEL_ID         = var.bedrock_model_id
    AWS_POLLY_ENGINE         = var.aws_polly_engine
    AWS_LOG_GROUP_NAME       = var.aws_log_group_name != "" ? var.aws_log_group_name : data.terraform_remote_state.infra.outputs.app_log_group_name
    AWS_LOG_STREAM_NAME      = var.aws_log_stream_name
    AWS_MONITORING_NAMESPACE = var.aws_monitoring_namespace
    VERTEX_AI_MODEL          = ""
  }
}

resource "kubernetes_config_map_v1" "scraped_alerts" {
  metadata {
    name      = "scraped-alerts"
    namespace = kubernetes_namespace_v1.app.metadata[0].name
  }

  data = {
    "scraped_alerts.json" = file("${path.module}/../../backend/data/scraped_alerts.json")
  }
}

resource "kubernetes_cluster_role_v1" "cluster_autoscaler" {
  metadata {
    name = "cluster-autoscaler"
  }

  rule {
    api_groups = [""]
    resources  = ["events", "endpoints"]
    verbs      = ["create", "patch"]
  }
  rule {
    api_groups = [""]
    resources  = ["pods/eviction"]
    verbs      = ["create"]
  }
  rule {
    api_groups = [""]
    resources  = ["pods/status"]
    verbs      = ["update"]
  }
  rule {
    api_groups     = [""]
    resources      = ["endpoints"]
    resource_names = ["cluster-autoscaler"]
    verbs          = ["get", "update"]
  }
  rule {
    api_groups = [""]
    resources  = ["nodes"]
    verbs      = ["watch", "list", "get", "update"]
  }
  rule {
    api_groups = [""]
    resources  = ["namespaces", "pods", "services", "replicationcontrollers", "persistentvolumeclaims", "persistentvolumes"]
    verbs      = ["watch", "list", "get"]
  }
  rule {
    api_groups = ["extensions"]
    resources  = ["replicasets", "daemonsets"]
    verbs      = ["watch", "list", "get"]
  }
  rule {
    api_groups = ["policy"]
    resources  = ["poddisruptionbudgets"]
    verbs      = ["watch", "list"]
  }
  rule {
    api_groups = ["apps"]
    resources  = ["statefulsets", "replicasets", "daemonsets"]
    verbs      = ["watch", "list", "get"]
  }
  rule {
    api_groups = ["storage.k8s.io"]
    resources  = ["storageclasses", "csinodes", "csidrivers", "csistoragecapacities"]
    verbs      = ["watch", "list", "get"]
  }
  rule {
    api_groups = ["batch", "extensions"]
    resources  = ["jobs"]
    verbs      = ["get", "list", "watch", "patch"]
  }
  rule {
    api_groups = ["coordination.k8s.io"]
    resources  = ["leases"]
    verbs      = ["create"]
  }
  rule {
    api_groups     = ["coordination.k8s.io"]
    resources      = ["leases"]
    resource_names = ["cluster-autoscaler"]
    verbs          = ["get", "update"]
  }
}

resource "kubernetes_cluster_role_binding_v1" "cluster_autoscaler" {
  metadata {
    name = "cluster-autoscaler"
  }

  role_ref {
    api_group = "rbac.authorization.k8s.io"
    kind      = "ClusterRole"
    name      = kubernetes_cluster_role_v1.cluster_autoscaler.metadata[0].name
  }

  subject {
    kind      = "ServiceAccount"
    name      = "cluster-autoscaler"
    namespace = kubernetes_namespace_v1.app.metadata[0].name
  }
}

resource "kubernetes_manifest" "app_resources" {
  for_each = {
    service_account_app         = local.rendered_resources[0]
    service_account_autoscaler  = local.rendered_resources[1]
    deployment_app              = local.rendered_resources[2]
    deployment_autoscaler       = local.rendered_resources[3]
    hpa_app                     = local.rendered_resources[4]
  }

  manifest = each.value

  depends_on = [
    kubernetes_namespace_v1.app,
    kubernetes_secret_v1.app_secret,
    kubernetes_config_map_v1.scraped_alerts,
    kubernetes_cluster_role_v1.cluster_autoscaler,
    kubernetes_cluster_role_binding_v1.cluster_autoscaler,
    aws_acm_certificate_validation.app,
  ]
}

resource "kubernetes_service_v1" "app" {
  metadata {
    name      = "anti-fraudx"
    namespace = kubernetes_namespace_v1.app.metadata[0].name
    annotations = merge(
      {
        "service.beta.kubernetes.io/aws-load-balancer-type"             = "nlb"
        "service.beta.kubernetes.io/aws-load-balancer-name"             = "${var.project_name}-anti-fraudx-nlb"
        "service.beta.kubernetes.io/aws-load-balancer-scheme"           = var.aws_load_balancer_scheme
        "service.beta.kubernetes.io/aws-load-balancer-backend-protocol" = "tcp"
      },
      local.effective_acm_certificate_arn != "" ? {
        "service.beta.kubernetes.io/aws-load-balancer-ssl-cert"  = local.effective_acm_certificate_arn
        "service.beta.kubernetes.io/aws-load-balancer-ssl-ports" = "443"
      } : {}
    )
  }

  spec {
    type = "LoadBalancer"

    selector = {
      app = "anti-fraudx"
    }

    port {
      name        = "http"
      port        = 80
      target_port = 8080
    }

    port {
      name        = "https"
      port        = 443
      target_port = 8080
    }
  }

  depends_on = [
    kubernetes_manifest.app_resources,
    aws_acm_certificate_validation.app,
  ]
}

resource "terraform_data" "wait_for_nlb" {
  count = var.domain_name != "" ? 1 : 0

  depends_on = [kubernetes_service_v1.app, terraform_data.update_kubeconfig]

  provisioner "local-exec" {
    interpreter = ["PowerShell", "-Command"]
    command = <<-EOT
      $maxAttempts = 30
      $sleepSeconds = 20
      for ($i = 1; $i -le $maxAttempts; $i++) {
        Write-Host "Waiting for Service LoadBalancer hostname... attempt $i/$maxAttempts"
        try {
          $json = kubectl get svc anti-fraudx -n anti-fraudx-terraform -o json 2>$null | ConvertFrom-Json
          $hostname = $json.status.loadBalancer.ingress[0].hostname
          if ($hostname) {
            Write-Host "LoadBalancer hostname found: $hostname"
            $hostname | Out-File -FilePath "$PWD/nlb_hostname.txt" -NoNewline -Encoding utf8
            exit 0
          }
        } catch {}
        Start-Sleep -Seconds $sleepSeconds
      }
      Write-Error "Service LoadBalancer hostname did not appear after $($maxAttempts * $sleepSeconds) seconds"
      exit 1
    EOT
  }
}

data "aws_lb" "anti_fraudx" {
  count = var.domain_name != "" ? 1 : 0

  tags = {
    "kubernetes.io/service-name" = "anti-fraudx-terraform/anti-fraudx"
  }

  depends_on = [terraform_data.wait_for_nlb]
}

resource "aws_route53_record" "app" {
  count   = var.domain_name != "" ? 1 : 0
  zone_id = data.terraform_remote_state.infra.outputs.route53_zone_id
  name    = var.domain_name
  type    = "A"

  alias {
    name                   = data.aws_lb.anti_fraudx[0].dns_name
    zone_id                = data.aws_lb.anti_fraudx[0].zone_id
    evaluate_target_health = true
  }
}

output "route53_record_fqdn" { value = var.domain_name != "" ? aws_route53_record.app[0].fqdn : "" }
output "aws_acm_certificate_effective_arn" { value = local.effective_acm_certificate_arn }
output "aws_host" { value = local.aws_host }
