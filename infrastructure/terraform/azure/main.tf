terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
  }
}

provider "azurerm" {
  features {}

  subscription_id = var.subscription_id
  tenant_id       = var.tenant_id
  client_id       = var.client_id
  client_secret   = var.client_secret
}

# ─── Resource Group ───────────────────────────────────────────────────────────
resource "azurerm_resource_group" "trading" {
  name     = "wingtradebot-rg"
  location = var.location

  tags = {
    Project = "wingtradebot"
    Env     = "production"
  }
}

# ─── Virtual Network + Subnet ─────────────────────────────────────────────────
resource "azurerm_virtual_network" "trading" {
  name                = "wingtradebot-vnet"
  address_space       = ["10.0.0.0/16"]
  location            = azurerm_resource_group.trading.location
  resource_group_name = azurerm_resource_group.trading.name
}

resource "azurerm_subnet" "trading" {
  name                 = "wingtradebot-subnet"
  resource_group_name  = azurerm_resource_group.trading.name
  virtual_network_name = azurerm_virtual_network.trading.name
  address_prefixes     = ["10.0.1.0/24"]
}

# ─── IP Público (equivalente ao Reserved IP DO / Elastic IP AWS) ──────────────
resource "azurerm_public_ip" "trading" {
  name                = "wingtradebot-pip"
  location            = azurerm_resource_group.trading.location
  resource_group_name = azurerm_resource_group.trading.name
  allocation_method   = "Static"
  sku                 = "Standard"

  tags = {
    Project = "wingtradebot"
  }
}

# ─── Network Security Group (equivalente ao Firewall DO / Security Group AWS) ─
resource "azurerm_network_security_group" "trading" {
  name                = "wingtradebot-nsg"
  location            = azurerm_resource_group.trading.location
  resource_group_name = azurerm_resource_group.trading.name

  # HTTPS — wingtradebot
  security_rule {
    name                       = "HTTPS"
    priority                   = 100
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "443"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  # HTTP — Let's Encrypt challenge / redirect
  security_rule {
    name                       = "HTTP"
    priority                   = 110
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "80"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  # SSH — porta customizada (não a 22)
  security_rule {
    name                       = "SSH-custom"
    priority                   = 120
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = tostring(var.ssh_port)
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  # ICMP — permite ping para diagnóstico
  security_rule {
    name                       = "ICMP"
    priority                   = 130
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Icmp"
    source_port_range          = "*"
    destination_port_range     = "*"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  tags = {
    Project = "wingtradebot"
  }
}

# ─── Network Interface ────────────────────────────────────────────────────────
resource "azurerm_network_interface" "trading" {
  name                = "wingtradebot-nic"
  location            = azurerm_resource_group.trading.location
  resource_group_name = azurerm_resource_group.trading.name

  ip_configuration {
    name                          = "internal"
    subnet_id                     = azurerm_subnet.trading.id
    private_ip_address_allocation = "Dynamic"
    public_ip_address_id          = azurerm_public_ip.trading.id
  }
}

# Associar NSG à NIC
resource "azurerm_network_interface_security_group_association" "trading" {
  network_interface_id      = azurerm_network_interface.trading.id
  network_security_group_id = azurerm_network_security_group.trading.id
}

# ─── VM (equivalente ao Droplet DO / EC2 AWS / VM GCP) ────────────────────────
resource "azurerm_linux_virtual_machine" "trading" {
  name                  = var.vm_name
  location              = azurerm_resource_group.trading.location
  resource_group_name   = azurerm_resource_group.trading.name
  size                  = var.vm_size
  admin_username        = "azureuser"
  network_interface_ids = [azurerm_network_interface.trading.id]

  admin_ssh_key {
    username   = "azureuser"
    public_key = var.ssh_public_key
  }

  os_disk {
    caching              = "ReadWrite"
    storage_account_type = "Standard_LRS"
    disk_size_gb         = 20
  }

  source_image_reference {
    publisher = "Canonical"
    offer     = "ubuntu-24_04-lts"
    sku       = "server"
    version   = "latest"
  }

  tags = {
    Project = "wingtradebot"
    Env     = "production"
  }
}
