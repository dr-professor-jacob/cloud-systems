variable "location" {
  description = "Azure region"
  type        = string
  default     = "southcentralus"
}

variable "admin_username" {
  description = "VM admin username"
  type        = string
  default     = "jrick"
}

variable "ssh_public_key_path" {
  description = "Path to SSH public key"
  type        = string
  default     = "../cloud-systems.pub"
}

variable "allowed_ssh_ip" {
  description = "CIDR allowed to SSH — deploy.sh overrides with caller's IP"
  type        = string
  default     = "0.0.0.0/0"
}
