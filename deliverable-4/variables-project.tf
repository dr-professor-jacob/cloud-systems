# Project-level variables: customize these in project.auto.tfvars

variable "resource_group_name" {
  description = "Name of the Azure resource group"
  type        = string
  default     = "deliverable-4"
}

variable "acr_name" {
  description = <<-EOT
    Azure Container Registry name.
    Must be globally unique, 5-50 characters, alphanumeric only (no hyphens).
    Suggestion: use your initials + 'subnets', e.g. 'jsmithsubnets'
  EOT
  type        = string

  validation {
    condition     = can(regex("^[a-zA-Z0-9]{5,50}$", var.acr_name))
    error_message = "ACR name must be 5-50 alphanumeric characters (no hyphens or underscores)."
  }
}

variable "app_name" {
  description = "Name for the Container App (lowercase alphanumeric and hyphens)"
  type        = string
  default     = "subnets"

  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9-]{1,30}[a-z0-9]$", var.app_name))
    error_message = "App name must be lowercase alphanumeric with hyphens, 3-32 characters."
  }
}

variable "image_tag" {
  description = "Container image tag to deploy (semantic version, e.g. 1.0.0)"
  type        = string
  default     = "latest"
}

variable "environment" {
  description = "Environment label applied to all resource tags"
  type        = string
  default     = "student-lab"
}
