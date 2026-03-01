output "instance_ip" {
  description = "IP público (Elastic IP) da instância"
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
