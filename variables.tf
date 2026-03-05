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
  default     = "*"
}

variable "domain_name" {
  description = "Your registered domain name (e.g. example.com). Leave null to use nip.io auto-domain from the public IP. Must be delegated to Azure DNS nameservers at your registrar before running Ansible."
  type        = string
  default     = null
}
