output "instance_ip" {
  description = "IP público (Elastic IP) da instância EC2"
  value       = aws_eip.trading.public_ip
}

output "instance_id" {
  description = "ID da instância EC2"
  value       = aws_instance.trading.id
}

output "ssh_command" {
  description = "Comando SSH para acessar a instância"
  value       = "ssh -p ${var.ssh_port} root@${aws_eip.trading.public_ip}"
}

# ─── RDS Outputs ──────────────────────────────────────────────────────────────

output "db_endpoint" {
  description = "RDS PostgreSQL endpoint (host:port) — use in DATABASE_URL"
  value       = aws_db_instance.trading.endpoint
}

output "db_host" {
  description = "RDS PostgreSQL hostname only (without port)"
  value       = aws_db_instance.trading.address
}

output "db_port" {
  description = "RDS PostgreSQL port"
  value       = aws_db_instance.trading.port
}

output "database_url" {
  description = "Full DATABASE_URL connection string — copy to .env or Ansible vars"
  value       = "postgres://${var.db_username}:${var.db_password}@${aws_db_instance.trading.endpoint}/wingtradebot"
  sensitive   = true
}

output "migration_command" {
  description = "Command to run the data migration tool after terraform apply"
  value       = "python tools/db_migrator.py --target aws --db-host ${aws_db_instance.trading.address} --db-user ${var.db_username} --db-name wingtradebot"
}
