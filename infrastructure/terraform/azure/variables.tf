variable "subscription_id" {
  description = "Azure Subscription ID"
  type        = string
}

variable "tenant_id" {
  description = "Azure Tenant ID (Active Directory)"
  type        = string
}

variable "client_id" {
  description = "Azure Service Principal Client ID (App Registration)"
  type        = string
}

variable "client_secret" {
  description = "Azure Service Principal Client Secret"
  type        = string
  sensitive   = true
}

variable "ssh_public_key" {
  description = "Conteúdo da chave pública SSH (nova_kygen.pub)"
  type        = string
}

variable "vm_name" {
  description = "Nome da VM"
  type        = string
  default     = "wingtradebot"
}

variable "location" {
  description = "Região Azure (East US é a mais barata)"
  type        = string
  default     = "eastus"
}

variable "vm_size" {
  description = "Tamanho da VM (Standard_B1ms ≈ 1 vCPU, 2 GB RAM)"
  type        = string
  default     = "Standard_B1ms"
}

variable "ssh_port" {
  description = "Porta SSH customizada (diferente de 22)"
  type        = number
  default     = 2277
}

# ─── Azure PostgreSQL Flexible Server Variables ───────────────────────────────

variable "db_username" {
  description = "PostgreSQL administrator login for Azure Database"
  type        = string
  default     = "wingbot"
}

variable "db_password" {
  description = "PostgreSQL administrator password (min 8 chars, must include uppercase, lowercase, number)"
  type        = string
  sensitive   = true
}

variable "migration_tool_start_ip" {
  description = <<-EOT
    Start of your local machine's public IP range for migration tool access.
    For a single IP, set this equal to migration_tool_end_ip.
    Find your IP: curl ifconfig.me
  EOT
  type    = string
  default = "0.0.0.0"
}

variable "migration_tool_end_ip" {
  description = <<-EOT
    End of your local machine's public IP range for migration tool access.
    For a single IP, set this equal to migration_tool_start_ip.
    Find your IP: curl ifconfig.me
  EOT
  type    = string
  default = "255.255.255.255"
}
