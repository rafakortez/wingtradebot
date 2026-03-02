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

# ─── Security Group — App (EC2) ───────────────────────────────────────────────
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

# ─── Security Group — RDS PostgreSQL ─────────────────────────────────────────
# Only allows inbound PostgreSQL (5432) from the EC2 app security group.
# The database is NOT publicly accessible — only the app can reach it.
resource "aws_security_group" "rds" {
  name        = "wingtradebot-rds-sg"
  description = "WingTradeBot RDS PostgreSQL - only accessible from app EC2"

  ingress {
    description     = "PostgreSQL from app"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.trading.id]
  }

  # Also allow from the migration tool running on your local machine
  # IMPORTANT: Replace with your actual local IP before running terraform apply
  # Find your IP: curl ifconfig.me
  ingress {
    description = "PostgreSQL from migration tool (your local IP)"
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = [var.migration_tool_ip]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name    = "wingtradebot-rds-sg"
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

# ─── RDS PostgreSQL — Minimal & Cheapest ─────────────────────────────────────
# db.t3.micro: 1 vCPU, 1 GB RAM — ~$10/month
# After migration: set publicly_accessible = false for security
resource "aws_db_instance" "trading" {
  identifier        = "wingtradebot-db"
  engine            = "postgres"
  engine_version    = "16"
  instance_class    = "db.t3.micro"  # Smallest: 1 vCPU, 1 GB RAM
  allocated_storage = 10             # GB — minimal for testing
  storage_type      = "gp3"          # gp3 is cheaper than gp2

  db_name  = "wingtradebot"
  username = var.db_username
  password = var.db_password

  # Security: only accessible from the app EC2 and migration tool
  vpc_security_group_ids = [aws_security_group.rds.id]

  # IMPORTANT: Set db_publicly_accessible = true ONLY during migration
  # After migration, set to false and run 'terraform apply' again
  publicly_accessible = var.db_publicly_accessible

  # Minimal configuration
  multi_az               = false
  backup_retention_period = 0  # Disable backups for testing (save $)
  skip_final_snapshot    = true

  tags = {
    Name    = "wingtradebot-db"
    Project = "wingtradebot"
    Env     = "production"
  }
}
