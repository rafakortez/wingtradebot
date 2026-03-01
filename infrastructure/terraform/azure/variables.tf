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
