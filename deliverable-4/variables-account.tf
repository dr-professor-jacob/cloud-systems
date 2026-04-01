# Account-level variables: set once per student via select-location.sh
# These are written to account.auto.tfvars automatically — do not edit by hand.

variable "subscription_id" {
  description = "Azure subscription ID"
  type        = string
  sensitive   = true

  validation {
    condition     = can(regex("^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", var.subscription_id))
    error_message = "Must be a valid GUID (e.g. 12345678-1234-1234-1234-123456789012)."
  }
}

variable "location" {
  description = "Azure region — set by select-location.sh"
  type        = string
}
