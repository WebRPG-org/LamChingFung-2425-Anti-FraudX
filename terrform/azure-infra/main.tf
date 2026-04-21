terraform {
  required_version = ">= 1.6.0"
  required_providers {
    azurerm = { source = "hashicorp/azurerm", version = "~> 3.100" }
    random  = { source = "hashicorp/random", version = "~> 3.6" }
  }
}

provider "azurerm" {
  features {
    resource_group {
      prevent_deletion_if_contains_resources = false
    }
  }
  skip_provider_registration = true
}

resource "terraform_data" "preflight" {
  provisioner "local-exec" {
    interpreter = ["PowerShell", "-Command"]
    command = <<-EOT
      $ErrorActionPreference = 'Stop';
      if (-not (Get-Command az -ErrorAction SilentlyContinue)) {
        throw 'Missing required tool for azure-infra: az'
      }
      az account show --output none;
      $providers = @(
        'Microsoft.Network',
        'Microsoft.ContainerService',
        'Microsoft.DBforPostgreSQL',
        'Microsoft.OperationalInsights',
        'Microsoft.OperationsManagement',
        'Microsoft.Insights',
        'Microsoft.CognitiveServices'
      );
      foreach ($provider in $providers) {
        az provider register --namespace $provider --wait --output none | Out-Null;
      }
    EOT
  }
}

resource "azurerm_resource_group" "rg" {
  name     = "${var.project_name}-rg"
  location = var.location

  depends_on = [terraform_data.preflight]
}

resource "azurerm_virtual_network" "vnet" {
  name                = "${var.project_name}-vnet"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  address_space       = [var.vnet_cidr]
}

resource "azurerm_subnet" "aks_a" {
  name                 = "aks-private-a"
  resource_group_name  = azurerm_resource_group.rg.name
  virtual_network_name = azurerm_virtual_network.vnet.name
  address_prefixes     = [var.aks_subnet_a_cidr]
}

resource "azurerm_subnet" "aks_b" {
  name                 = "aks-private-b"
  resource_group_name  = azurerm_resource_group.rg.name
  virtual_network_name = azurerm_virtual_network.vnet.name
  address_prefixes     = [var.aks_subnet_b_cidr]
}

resource "azurerm_subnet" "db" {
  name                 = "db-private"
  resource_group_name  = azurerm_resource_group.rg.name
  virtual_network_name = azurerm_virtual_network.vnet.name
  address_prefixes     = [var.db_subnet_cidr]

  delegation {
    name = "postgres-flexible-server"
    service_delegation {
      name    = "Microsoft.DBforPostgreSQL/flexibleServers"
      actions = ["Microsoft.Network/virtualNetworks/subnets/join/action"]
    }
  }
}

resource "azurerm_private_dns_zone" "postgres" {
  name                = "${var.project_name}.postgres.database.azure.com"
  resource_group_name = azurerm_resource_group.rg.name
}

resource "azurerm_private_dns_zone_virtual_network_link" "postgres" {
  name                  = "${var.project_name}-postgres-link"
  private_dns_zone_name = azurerm_private_dns_zone.postgres.name
  virtual_network_id    = azurerm_virtual_network.vnet.id
  resource_group_name   = azurerm_resource_group.rg.name
}

resource "azurerm_postgresql_flexible_server" "postgres" {
  name                          = "${var.project_name}-postgres"
  resource_group_name           = azurerm_resource_group.rg.name
  location                      = azurerm_resource_group.rg.location
  version                       = "15"
  delegated_subnet_id           = azurerm_subnet.db.id
  private_dns_zone_id           = azurerm_private_dns_zone.postgres.id
  public_network_access_enabled = false
  administrator_login           = var.db_user
  administrator_password        = var.db_password
  storage_mb                    = 32768
  sku_name                      = var.db_sku_name
  zone                          = "1"

  depends_on = [azurerm_private_dns_zone_virtual_network_link.postgres]
}

resource "azurerm_postgresql_flexible_server_database" "app" {
  name      = var.db_name
  server_id = azurerm_postgresql_flexible_server.postgres.id
  collation = "en_US.utf8"
  charset   = "UTF8"
}

resource "azurerm_log_analytics_workspace" "logs" {
  name                = "${var.project_name}-logs"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  sku                 = "PerGB2018"
  retention_in_days   = 30
}

resource "random_string" "suffix" {
  length  = 6
  upper   = false
  special = false
}

resource "azurerm_cognitive_account" "openai" {
  name                  = substr(replace("${var.project_name}${random_string.suffix.result}", "-", ""), 0, 24)
  location              = var.azure_openai_region
  resource_group_name   = azurerm_resource_group.rg.name
  kind                  = "OpenAI"
  sku_name              = "S0"
  custom_subdomain_name = substr(replace("${var.project_name}-${random_string.suffix.result}", "_", "-"), 0, 63)
}

resource "azurerm_cognitive_deployment" "openai" {
  name                 = var.azure_openai_deployment
  cognitive_account_id = azurerm_cognitive_account.openai.id

  model {
    format  = "OpenAI"
    name    = var.azure_openai_model_name
    version = var.azure_openai_model_version
  }

  scale {
    type = "Standard"
  }
}

resource "azurerm_cognitive_account" "speech" {
  name                  = substr(replace("${var.project_name}speech${random_string.suffix.result}", "-", ""), 0, 24)
  location              = azurerm_resource_group.rg.location
  resource_group_name   = azurerm_resource_group.rg.name
  kind                  = "SpeechServices"
  sku_name              = "S0"
  custom_subdomain_name = substr(replace("${var.project_name}-speech-${random_string.suffix.result}", "_", "-"), 0, 63)
}

resource "azurerm_kubernetes_cluster" "aks" {
  name                = "${var.project_name}-aks"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  dns_prefix          = "${var.project_name}-aks"

  default_node_pool {
    name                = "system"
    node_count          = 1
    vm_size             = var.node_vm_size
    vnet_subnet_id      = azurerm_subnet.aks_a.id
    min_count           = 1
    max_count           = 3
    enable_auto_scaling = true
  }

  identity { type = "SystemAssigned" }

  oms_agent {
    log_analytics_workspace_id = azurerm_log_analytics_workspace.logs.id
  }
}

resource "azurerm_kubernetes_cluster_node_pool" "workload" {
  name                  = "workload"
  kubernetes_cluster_id = azurerm_kubernetes_cluster.aks.id
  vm_size               = var.node_vm_size
  node_count            = 1
  enable_auto_scaling   = true
  min_count             = 1
  max_count             = 4
  vnet_subnet_id        = azurerm_subnet.aks_b.id
  mode                  = "User"
}

resource "azurerm_monitor_diagnostic_setting" "aks" {
  name                       = "${var.project_name}-aks-diagnostics"
  target_resource_id         = azurerm_kubernetes_cluster.aks.id
  log_analytics_workspace_id = azurerm_log_analytics_workspace.logs.id

  enabled_log {
    category = "kube-apiserver"
  }

  metric {
    category = "AllMetrics"
  }
}

resource "azurerm_dns_zone" "anti_fraudx" {
  count               = var.domain_name != "" ? 1 : 0
  name                = var.domain_name
  resource_group_name = azurerm_resource_group.rg.name
}

output "resource_group" { value = azurerm_resource_group.rg.name }
output "location" { value = azurerm_resource_group.rg.location }
output "aks_name" { value = azurerm_kubernetes_cluster.aks.name }
output "postgres_fqdn" { value = azurerm_postgresql_flexible_server.postgres.fqdn }
output "postgres_db_name" { value = azurerm_postgresql_flexible_server_database.app.name }
output "db_user" { value = var.db_user }
output "db_password" {
  value     = var.db_password
  sensitive = true
}
output "log_analytics_workspace_name" { value = azurerm_log_analytics_workspace.logs.name }
output "log_analytics_workspace_id" { value = azurerm_log_analytics_workspace.logs.workspace_id }
output "log_analytics_shared_key" {
  value     = azurerm_log_analytics_workspace.logs.primary_shared_key
  sensitive = true
}
output "azure_openai_endpoint" { value = azurerm_cognitive_account.openai.endpoint }
output "azure_openai_deployment" { value = azurerm_cognitive_deployment.openai.name }
output "azure_openai_api_version" { value = var.azure_openai_api_version }
output "azure_openai_api_key" {
  value     = azurerm_cognitive_account.openai.primary_access_key
  sensitive = true
}
output "azure_speech_endpoint" { value = azurerm_cognitive_account.speech.endpoint }
output "azure_speech_key" {
  value     = azurerm_cognitive_account.speech.primary_access_key
  sensitive = true
}
output "azure_speech_region" { value = var.azure_speech_region }
output "dns_zone_name" { value = var.domain_name != "" ? azurerm_dns_zone.anti_fraudx[0].name : "" }
output "azure_host" { value = var.domain_name != "" ? var.domain_name : "${var.project_name}.local" }
output "kube_host" {
  value     = azurerm_kubernetes_cluster.aks.kube_config[0].host
  sensitive = true
}
output "kube_username" {
  value     = azurerm_kubernetes_cluster.aks.kube_config[0].username
  sensitive = true
}
output "kube_password" {
  value     = azurerm_kubernetes_cluster.aks.kube_config[0].password
  sensitive = true
}
output "kube_client_certificate" {
  value     = azurerm_kubernetes_cluster.aks.kube_config[0].client_certificate
  sensitive = true
}
output "kube_client_key" {
  value     = azurerm_kubernetes_cluster.aks.kube_config[0].client_key
  sensitive = true
}
output "kube_cluster_ca_certificate" {
  value     = azurerm_kubernetes_cluster.aks.kube_config[0].cluster_ca_certificate
  sensitive = true
}
