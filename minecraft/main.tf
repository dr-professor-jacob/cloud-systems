terraform {
  backend "azurerm" {
    resource_group_name  = "tfstate-rg"
    storage_account_name = "cloudv3tfstate"
    container_name       = "tfstate"
    key                  = "minecraft.tfstate"
  }
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
  }
}

provider "azurerm" {
  features {}
}

# ── Resource group ────────────────────────────────────────────────────────────

resource "azurerm_resource_group" "mc" {
  name     = "minecraft-rg"
  location = var.location
}

# ── Networking ────────────────────────────────────────────────────────────────

resource "azurerm_virtual_network" "mc" {
  name                = "mc-vnet"
  address_space       = ["10.1.0.0/16"]
  location            = azurerm_resource_group.mc.location
  resource_group_name = azurerm_resource_group.mc.name
}

resource "azurerm_subnet" "mc" {
  name                 = "mc-subnet"
  resource_group_name  = azurerm_resource_group.mc.name
  virtual_network_name = azurerm_virtual_network.mc.name
  address_prefixes     = ["10.1.0.0/24"]
}

resource "azurerm_public_ip" "mc" {
  name                = "mc-pip"
  location            = azurerm_resource_group.mc.location
  resource_group_name = azurerm_resource_group.mc.name
  allocation_method   = "Static"
}

resource "azurerm_network_security_group" "mc" {
  name                = "mc-nsg"
  location            = azurerm_resource_group.mc.location
  resource_group_name = azurerm_resource_group.mc.name

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
    name                       = "AllowMinecraft"
    priority                   = 110
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "25565"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }
}

resource "azurerm_network_interface" "mc" {
  name                = "mc-nic"
  location            = azurerm_resource_group.mc.location
  resource_group_name = azurerm_resource_group.mc.name

  ip_configuration {
    name                          = "internal"
    subnet_id                     = azurerm_subnet.mc.id
    private_ip_address_allocation = "Dynamic"
    public_ip_address_id          = azurerm_public_ip.mc.id
  }
}

resource "azurerm_network_interface_security_group_association" "mc" {
  network_interface_id      = azurerm_network_interface.mc.id
  network_security_group_id = azurerm_network_security_group.mc.id
}

# ── Spot VM (ARM, 2 vCPU / 8 GB) ─────────────────────────────────────────────

resource "azurerm_linux_virtual_machine" "mc" {
  name                = "mc-vm"
  resource_group_name = azurerm_resource_group.mc.name
  location            = azurerm_resource_group.mc.location
  size                = "Standard_D2ps_v5"
  admin_username      = var.admin_username
  priority            = "Spot"
  eviction_policy     = "Deallocate"
  max_bid_price       = -1
  disable_password_authentication = true

  admin_ssh_key {
    username   = var.admin_username
    public_key = file(var.ssh_public_key_path)
  }

  network_interface_ids = [azurerm_network_interface.mc.id]

  os_disk {
    caching              = "ReadWrite"
    storage_account_type = "Standard_LRS"
    disk_size_gb         = 64
  }

  source_image_reference {
    publisher = "Canonical"
    offer     = "ubuntu-22_04-lts"
    sku       = "server-arm64"
    version   = "latest"
  }

  boot_diagnostics {}
}

# ── Auto-restart on eviction ──────────────────────────────────────────────────

resource "azurerm_automation_account" "mc" {
  name                = "mc-automation"
  location            = "eastus"
  resource_group_name = azurerm_resource_group.mc.name
  sku_name            = "Basic"

  identity {
    type = "SystemAssigned"
  }
}

resource "azurerm_role_assignment" "automation_vm_start" {
  scope                = azurerm_linux_virtual_machine.mc.id
  role_definition_name = "Virtual Machine Contributor"
  principal_id         = azurerm_automation_account.mc.identity[0].principal_id
}

resource "azurerm_automation_runbook" "mc_restart" {
  name                    = "mc-auto-restart"
  location                = "eastus"
  resource_group_name     = azurerm_resource_group.mc.name
  automation_account_name = azurerm_automation_account.mc.name
  log_verbose             = false
  log_progress            = false
  runbook_type            = "PowerShell"

  content = <<-SCRIPT
    Connect-AzAccount -Identity
    $vm = Get-AzVM -ResourceGroupName "minecraft-rg" -Name "mc-vm" -Status
    $state = ($vm.Statuses | Where-Object { $_.Code -like "PowerState/*" }).Code
    if ($state -ne "PowerState/running") {
      Write-Output "VM is $state — starting..."
      Start-AzVM -ResourceGroupName "minecraft-rg" -Name "mc-vm"
      Write-Output "Done."
    } else {
      Write-Output "VM already running."
    }
  SCRIPT
}

resource "azurerm_automation_webhook" "mc_restart" {
  name                    = "mc-restart-webhook"
  resource_group_name     = azurerm_resource_group.mc.name
  automation_account_name = azurerm_automation_account.mc.name
  expiry_time             = "2030-01-01T00:00:00Z"
  enabled                 = true
  runbook_name            = azurerm_automation_runbook.mc_restart.name
}

resource "azurerm_monitor_action_group" "mc_restart" {
  name                = "mc-restart-ag"
  resource_group_name = azurerm_resource_group.mc.name
  short_name          = "mc-restart"

  automation_runbook_receiver {
    name                    = "restart-runbook"
    automation_account_id   = azurerm_automation_account.mc.id
    runbook_name            = azurerm_automation_runbook.mc_restart.name
    webhook_resource_id     = azurerm_automation_webhook.mc_restart.id
    is_global_runbook       = false
    service_uri             = azurerm_automation_webhook.mc_restart.uri
    use_common_alert_schema = true
  }
}

resource "azurerm_monitor_activity_log_alert" "mc_deallocated" {
  name                = "mc-vm-deallocated"
  resource_group_name = azurerm_resource_group.mc.name
  location            = "global"
  scopes              = [azurerm_linux_virtual_machine.mc.id]
  description         = "Fires when spot VM is evicted — triggers auto-restart runbook"

  criteria {
    category       = "Administrative"
    operation_name = "Microsoft.Compute/virtualMachines/deallocate/action"
    level          = "Informational"
  }

  action {
    action_group_id = azurerm_monitor_action_group.mc_restart.id
  }
}

# ── Ansible inventory ─────────────────────────────────────────────────────────

resource "local_file" "ansible_inventory" {
  content = templatefile("${path.module}/inventory.tmpl", {
    public_ip = azurerm_public_ip.mc.ip_address
  })
  filename = "${path.module}/inventory.ini"
}
