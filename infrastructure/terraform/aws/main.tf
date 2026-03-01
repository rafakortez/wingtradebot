terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region     = var.region
  access_key = var.aws_access_key
  secret_key = var.aws_secret_key
}

# ─── Chave SSH ────────────────────────────────────────────────────────────────
resource "aws_key_pair" "trading" {
  key_name   = "wingtradebot-key"
  public_key = var.ssh_public_key
}

# ─── Security Group (equivalente ao Firewall DO / GCP) ────────────────────────
resource "aws_security_group" "trading" {
  name        = "wingtradebot-sg"
  description = "WingTradeBot - regras de firewall"

  # HTTPS — wingtradebot
  ingress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # HTTP — Let's Encrypt challenge / redirect
  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # SSH — porta customizada (não a 22)
  ingress {
    description = "SSH customizado"
    from_port   = var.ssh_port
    to_port     = var.ssh_port
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # ICMP — permite ping para diagnóstico
  ingress {
    description = "ICMP ping"
    from_port   = -1
    to_port     = -1
    protocol    = "icmp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Saída — tudo permitido (app chama APIs externas)
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name    = "wingtradebot-sg"
    Project = "wingtradebot"
  }
}

# ─── EC2 Instance (equivalente ao Droplet DO / VM GCP) ────────────────────────
resource "aws_instance" "trading" {
  ami                    = var.ami_id
  instance_type          = var.instance_type
  key_name               = aws_key_pair.trading.key_name
  vpc_security_group_ids = [aws_security_group.trading.id]

  root_block_device {
    volume_size = 20 # GB
    volume_type = "gp3"
  }

  tags = {
    Name    = var.instance_name
    Project = "wingtradebot"
    Env     = "production"
  }
}

# ─── Elastic IP (equivalente ao Reserved IP DO / Static IP GCP) ───────────────
resource "aws_eip" "trading" {
  instance = aws_instance.trading.id
  domain   = "vpc"

  tags = {
    Name    = "wingtradebot-eip"
    Project = "wingtradebot"
  }
}
