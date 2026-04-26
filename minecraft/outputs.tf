output "public_ip" {
  value       = azurerm_public_ip.mc.ip_address
  description = "Connect at <ip>:25565"
}

output "ssh_command" {
  value       = "ssh -i ./cloud-systems ${azurerm_linux_virtual_machine.mc.admin_username}@${azurerm_public_ip.mc.ip_address}"
  description = "SSH into the server"
}
