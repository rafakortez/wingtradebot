variable "do_token" {
  description = "DigitalOcean API token (generate at: https://cloud.digitalocean.com/account/api/tokens)"
  type        = string
  sensitive   = true
}

variable "ssh_public_key" {
  description = "SSH public key contents"
  type        = string
}

variable "droplet_name" {
  description = "Droplet name"
  type        = string
  default     = "VM-ubuntu"
}

variable "region" {
  description = "DigitalOcean region"
  type        = string
  default     = "nyc1"
}

variable "droplet_size" {
  description = "Droplet size (s-1vcpu-2gb = 1 vCPU, 2 GB RAM)"
  type        = string
  default     = "s-1vcpu-2gb"
}

variable "ssh_port" {
  description = "Custom SSH port (non-default)"
  type        = number
  default     = 2277
}
