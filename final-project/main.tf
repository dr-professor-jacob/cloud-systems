terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
  }
}

provider "azurerm" {
  features {}
  subscription_id = var.subscription_id
}

data "azurerm_client_config" "current" {}

locals {
  tags = {
    project    = "rf-survey"
    managed_by = "opentofu"
  }
  # Use placeholder image until first build-push.sh run
  worker_image = var.image_tag_worker == "placeholder" ? "mcr.microsoft.com/azuredocs/containerapps-helloworld:latest" : "${azurerm_container_registry.main.login_server}/rf-worker:${var.image_tag_worker}"
  sb_fqn       = "${azurerm_servicebus_namespace.main.name}.servicebus.windows.net"
  storage_url  = "https://${azurerm_storage_account.main.name}.blob.core.windows.net"
}

# ---------------------------------------------------------------------------
# Resource Group
# ---------------------------------------------------------------------------
resource "azurerm_resource_group" "main" {
  name     = var.resource_group_name
  location = var.location
  tags     = local.tags
}

# ---------------------------------------------------------------------------
# Service Bus Namespace + Queues
# ---------------------------------------------------------------------------
resource "azurerm_servicebus_namespace" "main" {
  name                = "${var.project_name}-bus"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  sku                 = "Standard"
  tags                = local.tags
}

resource "azurerm_servicebus_queue" "sweeps" {
  name         = "rf-sweeps"
  namespace_id = azurerm_servicebus_namespace.main.id

  default_message_ttl   = "PT5M"   # 5 minutes — stale sweeps discarded
  max_size_in_megabytes = 1024
}

resource "azurerm_servicebus_queue" "commands" {
  name         = "rf-commands"
  namespace_id = azurerm_servicebus_namespace.main.id

  default_message_ttl   = "PT10M"  # 10 minutes — decode jobs expire
  max_size_in_megabytes = 1024
}

resource "azurerm_servicebus_queue" "results" {
  name         = "rf-results"
  namespace_id = azurerm_servicebus_namespace.main.id

  default_message_ttl   = "PT1H"   # 1 hour — results linger for polling
  max_size_in_megabytes = 1024
}

# ---------------------------------------------------------------------------
# SAS rules
# pi-edge: Pi sends sweeps/results, receives commands
# keda-listen: listen-only, used by Container App KEDA scaler
# ---------------------------------------------------------------------------
resource "azurerm_servicebus_namespace_authorization_rule" "pi" {
  name         = "pi-edge"
  namespace_id = azurerm_servicebus_namespace.main.id
  listen       = true
  send         = true
  manage       = false
}

resource "azurerm_servicebus_namespace_authorization_rule" "keda" {
  name         = "keda-listen"
  namespace_id = azurerm_servicebus_namespace.main.id
  listen       = true
  send         = false
  manage       = false
}

# ---------------------------------------------------------------------------
# Storage Account + Containers
# ---------------------------------------------------------------------------
resource "azurerm_storage_account" "main" {
  name                     = "${var.project_name}storage"
  resource_group_name      = azurerm_resource_group.main.name
  location                 = azurerm_resource_group.main.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  tags                     = local.tags
}

resource "azurerm_storage_container" "sweeps" {
  name                  = "rfsweeps"
  storage_account_id    = azurerm_storage_account.main.id
  container_access_type = "private"
}

resource "azurerm_storage_container" "results" {
  name                  = "rfresults"
  storage_account_id    = azurerm_storage_account.main.id
  container_access_type = "private"
}

# ---------------------------------------------------------------------------
# Azure Container Registry
# ---------------------------------------------------------------------------
resource "azurerm_container_registry" "main" {
  name                = var.acr_name
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = "Basic"
  admin_enabled       = false
  tags                = local.tags
}

# ---------------------------------------------------------------------------
# Container Apps Environment
# ---------------------------------------------------------------------------
resource "azurerm_container_app_environment" "main" {
  name                = "${var.project_name}-env"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  logs_destination    = ""
  tags                = local.tags
}

# ---------------------------------------------------------------------------
# User-Assigned Managed Identity + Role Assignments
# ---------------------------------------------------------------------------
resource "azurerm_user_assigned_identity" "main" {
  name                = "${var.project_name}-identity"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  tags                = local.tags
}

resource "azurerm_role_assignment" "acr_pull" {
  scope                = azurerm_container_registry.main.id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_user_assigned_identity.main.principal_id
}

resource "azurerm_role_assignment" "sb_owner" {
  scope                = azurerm_servicebus_namespace.main.id
  role_definition_name = "Azure Service Bus Data Owner"
  principal_id         = azurerm_user_assigned_identity.main.principal_id
}

resource "azurerm_role_assignment" "blob_contrib" {
  scope                = azurerm_storage_account.main.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_user_assigned_identity.main.principal_id
}

# ---------------------------------------------------------------------------
# Role assignments for the existing app VM's managed identity
# so rf-web (running on the VM) can access Service Bus + Blob
# ---------------------------------------------------------------------------
resource "azurerm_role_assignment" "vm_sb" {
  count                = var.vm_identity_principal_id != "" ? 1 : 0
  scope                = azurerm_servicebus_namespace.main.id
  role_definition_name = "Azure Service Bus Data Owner"
  principal_id         = var.vm_identity_principal_id
}

resource "azurerm_role_assignment" "vm_blob" {
  count                = var.vm_identity_principal_id != "" ? 1 : 0
  scope                = azurerm_storage_account.main.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = var.vm_identity_principal_id
}

# ---------------------------------------------------------------------------
# Container App: rf-worker
# No ingress — processes queues in background.
# ---------------------------------------------------------------------------
resource "azurerm_container_app" "worker" {
  name                         = "rf-worker"
  container_app_environment_id = azurerm_container_app_environment.main.id
  resource_group_name          = azurerm_resource_group.main.name
  revision_mode                = "Single"

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.main.id]
  }

  registry {
    server   = azurerm_container_registry.main.login_server
    identity = azurerm_user_assigned_identity.main.id
  }

  secret {
    name  = "anthropic-key"
    value = var.anthropic_api_key
  }

  # KEDA needs a connection string secret (managed identity not supported for KEDA SB trigger)
  secret {
    name  = "sb-keda-conn"
    value = azurerm_servicebus_namespace_authorization_rule.keda.primary_connection_string
  }

  template {
    min_replicas = 0
    max_replicas = 3

    # KEDA autoscale: scale out when rf-sweeps queue depth > 5 messages.
    # Pi off → 0 replicas ($0). Pi on → queue fills → worker scales 1→3.
    custom_scale_rule {
      name             = "sb-sweeps-queue"
      custom_rule_type = "azure-servicebus"
      metadata = {
        queueName    = azurerm_servicebus_queue.sweeps.name
        namespace    = azurerm_servicebus_namespace.main.name
        messageCount = "5"
      }
      authentication {
        secret_ref        = "sb-keda-conn"
        trigger_parameter = "connection"
      }
    }

    container {
      name   = "rf-worker"
      image  = local.worker_image
      cpu    = 0.5
      memory = "1Gi"

      env {
        name  = "SERVICE_BUS_NAMESPACE"
        value = local.sb_fqn
      }
      env {
        name  = "STORAGE_ACCOUNT_URL"
        value = local.storage_url
      }
      env {
        name  = "AZURE_CLIENT_ID"
        value = azurerm_user_assigned_identity.main.client_id
      }
    }
  }

  tags       = local.tags
  depends_on = [azurerm_role_assignment.acr_pull, azurerm_role_assignment.sb_owner, azurerm_role_assignment.blob_contrib]
}

# ---------------------------------------------------------------------------
# Outputs
# ---------------------------------------------------------------------------
output "acr_login_server" {
  value       = azurerm_container_registry.main.login_server
  description = "ACR hostname — used by build-push.sh"
}

output "sb_pi_connection_string" {
  value       = azurerm_servicebus_namespace_authorization_rule.pi.primary_connection_string
  description = "Service Bus connection string for Pi edge node — store in KV after apply"
  sensitive   = true
}

output "sb_namespace_fqn" {
  value       = local.sb_fqn
  description = "Service Bus FQDN — store as KV secret rf-sb-namespace for VM"
}

output "storage_account_url" {
  value       = local.storage_url
  description = "Blob Storage URL — store as KV secret rf-storage-url for VM"
}

output "resource_group_name" {
  value = azurerm_resource_group.main.name
}

output "storage_account_name" {
  value       = azurerm_storage_account.main.name
  description = "Storage account name — used by deploy.sh to fetch connection string for Pi"
}

output "sb_keda_connection_string" {
  value       = azurerm_servicebus_namespace_authorization_rule.keda.primary_connection_string
  description = "Listen-only Service Bus connection string used by KEDA scaler"
  sensitive   = true
}
