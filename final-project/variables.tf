variable "subscription_id" {
  description = "Azure subscription ID"
  type        = string
  sensitive   = true
  validation {
    condition     = can(regex("^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", var.subscription_id))
    error_message = "Must be a valid GUID."
  }
}

variable "location" {
  description = "Azure region"
  type        = string
  default     = "eastus"
}

variable "resource_group_name" {
  description = "Resource group name"
  type        = string
  default     = "rf-survey-rg"
}

variable "project_name" {
  description = "Short prefix for resource names (3-8 chars, lowercase alphanumeric)"
  type        = string
  default     = "rfsrvy"
  validation {
    condition     = can(regex("^[a-z0-9]{3,8}$", var.project_name))
    error_message = "project_name must be 3-8 lowercase alphanumeric characters (used in storage account name)."
  }
}

variable "acr_name" {
  description = "Azure Container Registry name (globally unique, alphanumeric, 5-50 chars)"
  type        = string
}

variable "image_tag_worker" {
  description = "Docker image tag for rf-worker container (use 'placeholder' until first build)"
  type        = string
  default     = "placeholder"
}

variable "vm_identity_principal_id" {
  description = "Principal ID of the app VM's managed identity (run: az vm identity show -n <vm> -g <rg> --query principalId -o tsv)"
  type        = string
  default     = ""
}

variable "container_app_env_name" {
  description = "Name of existing Container App Environment to reuse (student sub: 1 per region)"
  type        = string
}

variable "container_app_env_rg" {
  description = "Resource group containing the existing Container App Environment"
  type        = string
}

variable "anthropic_api_key" {
  description = "Anthropic API key for Claude integration"
  type        = string
  sensitive   = true
}
