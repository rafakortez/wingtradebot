variable "aws_access_key" {
  description = "AWS Access Key ID (gerar em: IAM > Users > Security Credentials)"
  type        = string
  sensitive   = true
}

variable "aws_secret_key" {
  description = "AWS Secret Access Key"
  type        = string
  sensitive   = true
}

variable "ssh_public_key" {
  description = "Conteúdo da chave pública SSH (nova_kygen.pub)"
  type        = string
}

variable "instance_name" {
  description = "Nome da instância EC2"
  type        = string
  default     = "wingtradebot"
}

variable "region" {
  description = "Região AWS"
  type        = string
  default     = "us-east-1"
}

variable "instance_type" {
  description = "EC2 instance type (t3.small = 1 vCPU, 2 GB RAM — matches your live server)"
  type        = string
  default     = "t3.small"  # 1 vCPU, 2 GB RAM — same as your live server
}

variable "ami_id" {
  description = "AMI Ubuntu 24.04 LTS (varia por região — us-east-1 default)"
  type        = string
  default     = "ami-0a0e5d9c7acc336f1" # Ubuntu 24.04 LTS us-east-1
}

variable "ssh_port" {
  description = "Porta SSH customizada (diferente de 22)"
  type        = number
  default     = 2277
}

# ─── RDS PostgreSQL Variables ─────────────────────────────────────────────────

variable "db_username" {
  description = "PostgreSQL master username for RDS"
  type        = string
  default     = "wingbot"
}

variable "db_password" {
  description = "PostgreSQL master password for RDS (min 8 chars, no @/)"
  type        = string
  sensitive   = true
}

variable "db_publicly_accessible" {
  description = <<-EOT
    Allow RDS to be accessed from the public internet.
    Set to true during initial data migration from your laptop.
    Set to false after migration is complete (more secure).
  EOT
  type    = bool
  default = true
}

variable "migration_tool_ip" {
  description = <<-EOT
    Your local machine's public IP in CIDR notation (e.g. "203.0.113.5/32").
    Used to allow the db_migrator.py tool to connect to RDS from your laptop.
    Find your IP: curl ifconfig.me
  EOT
  type    = string
  default = "0.0.0.0/0" # Restrict this to your actual IP for security
}
