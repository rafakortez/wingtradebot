variable "gcp_project" {
  description = "GCP Project ID"
  type        = string
}

variable "gcp_credentials_file" {
  description = "Path to GCP Service Account JSON credentials file"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "us-central1"
}

variable "zone" {
  description = "GCP zone (us-central1-a is free tier eligible)"
  type        = string
  default     = "us-central1-a"
}

variable "machine_type" {
  description = "VM machine type (e2-micro = free tier, e2-small = 2 GB RAM)"
  type        = string
  default     = "e2-small"
}

variable "ssh_public_key" {
  description = "SSH public key contents"
  type        = string
}

variable "ssh_port" {
  description = "Custom SSH port (non-default)"
  type        = number
  default     = 2277
}

# ─── Cloud SQL Variables ──────────────────────────────────────────────────────

variable "db_username" {
  description = "PostgreSQL username for Cloud SQL"
  type        = string
  default     = "wingbot"
}

variable "db_password" {
  description = "PostgreSQL password for Cloud SQL"
  type        = string
  sensitive   = true
}

variable "migration_tool_ip" {
  description = <<-EOT
    Your local machine's public IP in CIDR notation (e.g. "203.0.113.5/32").
    Used to allow the db_migrator.py tool to connect to Cloud SQL from your laptop.
    Find your IP: curl ifconfig.me
  EOT
  type    = string
  default = "0.0.0.0/0" # Restrict this to your actual IP for security
}
