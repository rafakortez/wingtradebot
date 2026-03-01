output "reserved_ip" {
  description = "Static IP address (use for DNS and Ansible inventory)"
  value       = digitalocean_reserved_ip.trading.ip_address
}

output "droplet_id" {
  description = "DigitalOcean Droplet ID"
  value       = digitalocean_droplet.trading.id
}

output "ssh_command" {
  description = "SSH connection command"
  value       = "ssh -p ${var.ssh_port} root@${digitalocean_reserved_ip.trading.ip_address}"
}
