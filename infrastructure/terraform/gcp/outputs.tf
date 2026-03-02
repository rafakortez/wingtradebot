output "public_ip" {
  description = "VM public IP address (use for DNS and Ansible inventory)"
  value       = google_compute_address.trading.address
}

output "ssh_command" {
  description = "SSH connection command"
  value       = "ssh -p ${var.ssh_port} root@${google_compute_address.trading.address}"
}

output "update_duckdns" {
  description = "DuckDNS update URL (replace YOUR_TOKEN and YOUR_DOMAIN)"
  value       = "https://www.duckdns.org/update?domains=YOUR_DOMAIN&token=YOUR_TOKEN&ip=${google_compute_address.trading.address}"
}

# ─── Cloud SQL Outputs ────────────────────────────────────────────────────────

output "db_public_ip" {
  description = "Cloud SQL PostgreSQL public IP address"
  value       = google_sql_database_instance.trading.public_ip_address
}

output "db_connection_name" {
  description = "Cloud SQL connection name (for Cloud SQL Proxy)"
  value       = google_sql_database_instance.trading.connection_name
}

output "database_url" {
  description = "Full DATABASE_URL connection string — copy to .env or Ansible vars"
  value       = "postgres://${var.db_username}:${var.db_password}@${google_sql_database_instance.trading.public_ip_address}:5432/wingtradebot"
  sensitive   = true
}

output "migration_command" {
  description = "Command to run the data migration tool after terraform apply"
  value       = "python tools/db_migrator.py --target gcp --db-host ${google_sql_database_instance.trading.public_ip_address} --db-user ${var.db_username} --db-name wingtradebot"
}
