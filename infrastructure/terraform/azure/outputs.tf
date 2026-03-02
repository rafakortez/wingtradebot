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

# ─── Azure PostgreSQL Outputs ─────────────────────────────────────────────────

output "db_fqdn" {
  description = "Azure PostgreSQL Flexible Server FQDN (hostname)"
  value       = azurerm_postgresql_flexible_server.trading.fqdn
}

output "database_url" {
  description = "Full DATABASE_URL connection string — copy to .env or Ansible vars"
  value       = "postgres://${var.db_username}:${var.db_password}@${azurerm_postgresql_flexible_server.trading.fqdn}:5432/wingtradebot"
  sensitive   = true
}

output "migration_command" {
  description = "Command to run the data migration tool after terraform apply"
  value       = "python tools/db_migrator.py --target azure --db-host ${azurerm_postgresql_flexible_server.trading.fqdn} --db-user ${var.db_username} --db-name wingtradebot"
}
