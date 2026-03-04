output "app_public_ip" {
  description = "Public IP address of the app VM"
  value       = azurerm_public_ip.app_pip.ip_address
}

output "db_private_ip" {
  description = "Private IP address of the DB VM"
  value       = azurerm_network_interface.db_nic.private_ip_address
}
