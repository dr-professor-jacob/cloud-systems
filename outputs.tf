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

output "db_private_ip" {
  description = "Private IP address of the DB VM"
  value       = azurerm_network_interface.db_nic.private_ip_address
}

output "dns_nameservers" {
  description = "Azure DNS nameservers — point your registrar's NS records here, then submit the DS record for DNSSEC"
  value       = var.domain_name != null ? azurerm_dns_zone.main[0].name_servers : []
}
