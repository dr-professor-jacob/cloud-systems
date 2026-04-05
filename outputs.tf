output "app_domain" {
  description = "Active domain for the app (real domain or nip.io fallback)"
  value       = local.app_domain
}

output "key_vault_name" {
  description = "Azure Key Vault name (stores Ansible Vault password)"
  value       = azurerm_key_vault.kv.name
}

output "app_public_ip" {
  description = "Public IP address of the app VM"
  value       = azurerm_public_ip.app_pip.ip_address
}

