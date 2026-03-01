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
