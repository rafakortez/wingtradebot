output "vm_public_ip" {
  description = "IP público (estático) da VM"
  value       = azurerm_public_ip.trading.ip_address
}

output "vm_id" {
  description = "ID da VM Azure"
  value       = azurerm_linux_virtual_machine.trading.id
}

output "ssh_command" {
  description = "Comando SSH para acessar a VM"
  value       = "ssh -p ${var.ssh_port} azureuser@${azurerm_public_ip.trading.ip_address}"
}
