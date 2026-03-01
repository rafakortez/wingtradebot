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
  description = "Tipo de instância EC2 (t3.small ≈ 1 vCPU, 2 GB RAM)"
  type        = string
  default     = "t3.small"
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
