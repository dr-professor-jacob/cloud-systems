terraform {
  backend "azurerm" {
    resource_group_name  = "tfstate-rg"
    storage_account_name = "cloudv3tfstate"
    container_name       = "tfstate"
    key                  = "cloud-systems.tfstate"
  }
  required_providers {
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 4.0"
    }
  }
}

provider "cloudflare" {}

provider "azurerm" {
  features {}
}

resource "azurerm_resource_group" "rg" {
  name     = "cloud-v3"
  location = var.location
}

resource "azurerm_virtual_network" "vnet" {
  name                = "cloud-vnet"
  address_space       = ["10.0.0.0/16"]
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
}

resource "azurerm_subnet" "app_subnet" {
  name                 = "app-subnet"
  resource_group_name  = azurerm_resource_group.rg.name
  virtual_network_name = azurerm_virtual_network.vnet.name
  address_prefixes     = ["10.0.1.0/24"]
}

resource "azurerm_public_ip" "app_pip" {
  name                = "app-pip"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  allocation_method   = "Static"
}

resource "azurerm_network_security_group" "app_nsg" {
  name                = "app-nsg"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name

  security_rule {
    name                       = "AllowSSH"
    priority                   = 100
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "22"
    source_address_prefix      = var.allowed_ssh_ip
    destination_address_prefix = "*"
  }


  security_rule {
    name                       = "AllowHTTP"
    priority                   = 110
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "80"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  security_rule {
    name                       = "AllowHTTPS"
    priority                   = 120
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "443"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  security_rule {
    name                       = "AllowTS3Voice"
    priority                   = 130
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Udp"
    source_port_range          = "*"
    destination_port_range     = "9987"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  security_rule {
    name                       = "AllowTS3Query"
    priority                   = 140
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_ranges    = ["10011", "10022"]
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  security_rule {
    name                       = "AllowTS3FileTransfer"
    priority                   = 150
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "30033"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }
}

resource "azurerm_network_interface" "app_nic" {
  name                = "app-nic"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name

  ip_configuration {
    name                          = "internal"
    subnet_id                     = azurerm_subnet.app_subnet.id
    private_ip_address_allocation = "Dynamic"
    public_ip_address_id          = azurerm_public_ip.app_pip.id
  }
}

resource "azurerm_network_interface_security_group_association" "app_nsg_assoc" {
  network_interface_id      = azurerm_network_interface.app_nic.id
  network_security_group_id = azurerm_network_security_group.app_nsg.id
}

resource "azurerm_linux_virtual_machine" "app_vm" {
  name                = "app-vm"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  size                = "Standard_B2pts_v2"
  admin_username      = var.admin_username
  disable_password_authentication = true

  admin_ssh_key {
    username   = var.admin_username
    public_key = file("mits_key.pub")
  }

  network_interface_ids = [azurerm_network_interface.app_nic.id]

  os_disk {
    caching              = "ReadWrite"
    storage_account_type = "Standard_LRS"
  }

  source_image_reference {
    publisher = "Canonical"
    offer     = "ubuntu-24_04-lts"
    sku       = "server-arm64"
    version   = "latest"
  }

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.app_vm.id]
  }

  boot_diagnostics {}
}

# ── Azure Key Vault (Ansible Vault password at rest) ────────────────────────

data "azurerm_client_config" "current" {}

# User-assigned identity created before KV and VM so principal_id is known at plan time
resource "azurerm_user_assigned_identity" "app_vm" {
  name                = "app-vm-identity"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
}

resource "azurerm_key_vault" "kv" {
  name                       = "cloud-v3-kv"
  location                   = azurerm_resource_group.rg.location
  resource_group_name        = azurerm_resource_group.rg.name
  tenant_id                  = data.azurerm_client_config.current.tenant_id
  sku_name                   = "standard"
  soft_delete_retention_days = 7
  purge_protection_enabled   = false

  access_policy {
    tenant_id = data.azurerm_client_config.current.tenant_id
    object_id = data.azurerm_client_config.current.object_id

    secret_permissions = ["Get", "Set", "List", "Delete", "Purge"]
  }

  access_policy {
    tenant_id = data.azurerm_client_config.current.tenant_id
    object_id = azurerm_user_assigned_identity.app_vm.principal_id

    secret_permissions = ["Get"]
  }
}

resource "random_password" "mcp_api_key" {
  length  = 64
  special = false
}

resource "azurerm_key_vault_secret" "mcp_api_key" {
  name         = "mcp-api-key"
  value        = random_password.mcp_api_key.result
  key_vault_id = azurerm_key_vault.kv.id
}

# ── Azure Monitor ────────────────────────────────────────────────────────────

resource "azurerm_monitor_action_group" "ops" {
  name                = "cloud-v3-ops"
  resource_group_name = azurerm_resource_group.rg.name
  short_name          = "ops"

  email_receiver {
    name          = "admin"
    email_address = "jr521816@ohio.edu"
  }
}

resource "azurerm_monitor_metric_alert" "app_cpu" {
  name                = "app-cpu-high"
  resource_group_name = azurerm_resource_group.rg.name
  scopes              = [azurerm_linux_virtual_machine.app_vm.id]
  description         = "App VM CPU > 85% sustained for 5 minutes"
  severity            = 2
  frequency           = "PT1M"
  window_size         = "PT5M"

  criteria {
    metric_namespace = "Microsoft.Compute/virtualMachines"
    metric_name      = "Percentage CPU"
    aggregation      = "Average"
    operator         = "GreaterThan"
    threshold        = 85
  }

  action {
    action_group_id = azurerm_monitor_action_group.ops.id
  }
}

resource "local_file" "ansible_inventory" {
  content = templatefile("inventory.tmpl", {
    public_ip = azurerm_public_ip.app_pip.ip_address
  })
  filename = "inventory.ini"
}

locals {
  app_domain = var.domain_name
}

resource "local_file" "ansible_vars" {
  content  = "app_domain: \"${local.app_domain}\"\n"
  filename = "group_vars/all/terraform_outputs.yml"
}

# ── Cloudflare DNS ────────────────────────────────────────────────────────────

resource "cloudflare_record" "app" {
  zone_id = var.cloudflare_zone_id
  name    = "@"
  content = azurerm_public_ip.app_pip.ip_address
  type    = "A"
  ttl     = 60
  proxied = false
}

resource "cloudflare_record" "ts" {
  zone_id = var.cloudflare_zone_id
  name    = "ts"
  content = azurerm_public_ip.app_pip.ip_address
  type    = "A"
  ttl     = 60
  proxied = false
}
