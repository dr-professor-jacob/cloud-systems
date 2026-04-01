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

locals {
  common_tags = {
    environment = var.environment
    managed_by  = "opentofu"
    project     = "deliverable-4-subnets"
  }

  # Use the hello-world placeholder until the student's image has been pushed.
  # After running build-push.sh and re-applying with image_tag set, this switches
  # to the ACR image automatically.
  container_image = var.image_tag == "latest" ? "mcr.microsoft.com/azuredocs/containerapps-helloworld:latest" : "${azurerm_container_registry.main.login_server}/${var.app_name}:${var.image_tag}"
}

# ---------------------------------------------------------------------------
# Resource Group
# ---------------------------------------------------------------------------
resource "azurerm_resource_group" "main" {
  name     = var.resource_group_name
  location = var.location
  tags     = local.common_tags
}

# ---------------------------------------------------------------------------
# Azure Container Registry
# Admin account is DISABLED — image pulls use Managed Identity only.
# ---------------------------------------------------------------------------
resource "azurerm_container_registry" "main" {
  name                = var.acr_name
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = "Basic"
  admin_enabled       = false

  tags = local.common_tags
}

# ---------------------------------------------------------------------------
# Log Analytics Workspace
# ---------------------------------------------------------------------------
resource "azurerm_log_analytics_workspace" "main" {
  name                = "${var.app_name}-logs"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  sku                 = "PerGB2018"
  retention_in_days   = 30

  tags = local.common_tags
}

# ---------------------------------------------------------------------------
# User-Assigned Managed Identity + AcrPull role
# ---------------------------------------------------------------------------
resource "azurerm_user_assigned_identity" "main" {
  name                = "${var.app_name}-identity"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name

  tags = local.common_tags
}

resource "azurerm_role_assignment" "acr_pull" {
  scope                = azurerm_container_registry.main.id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_user_assigned_identity.main.principal_id
}

# ---------------------------------------------------------------------------
# Container Apps Environment
# ---------------------------------------------------------------------------
resource "azurerm_container_app_environment" "main" {
  name                       = "${var.app_name}-env"
  location                   = azurerm_resource_group.main.location
  resource_group_name        = azurerm_resource_group.main.name
  log_analytics_workspace_id = azurerm_log_analytics_workspace.main.id

  tags = local.common_tags
}

# ---------------------------------------------------------------------------
# Container App
# image_tag controls which image is running.  Run build-push.sh first,
# then re-apply with -var image_tag=<version> to deploy or roll back.
# ---------------------------------------------------------------------------
resource "azurerm_container_app" "main" {
  name                         = var.app_name
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

  template {
    container {
      name   = var.app_name
      image  = local.container_image
      cpu    = 0.25
      memory = "0.5Gi"
    }
  }

  ingress {
    external_enabled = true
    target_port      = 80
    transport        = "http"

    traffic_weight {
      percentage      = 100
      latest_revision = true
    }
  }

  tags = local.common_tags

  depends_on = [azurerm_role_assignment.acr_pull]
}

# ---------------------------------------------------------------------------
# Outputs
# ---------------------------------------------------------------------------
output "acr_login_server" {
  value       = azurerm_container_registry.main.login_server
  description = "ACR hostname — used by build-push.sh"
}

output "app_url" {
  value       = "https://${azurerm_container_app.main.ingress[0].fqdn}"
  description = "Public HTTPS URL of the deployed application"
}

output "resource_group_name" {
  value       = azurerm_resource_group.main.name
  description = "Resource group — use this with tofu destroy to clean up"
}

output "log_analytics_workspace" {
  value       = azurerm_log_analytics_workspace.main.name
  description = "Log Analytics workspace name"
}
