variable "location" {
  description = "Azure region for all resources"
  type        = string
  default     = "southcentralus"
}

variable "admin_username" {
  description = "Admin username for VM SSH access"
  type        = string
  default     = "jrick"
}

variable "allowed_ssh_ip" {
  description = "CIDR of the host allowed to SSH to the app VM"
  type        = string
  default     = "75.188.18.74/32"
}
