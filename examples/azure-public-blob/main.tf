terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "=4.14.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

provider "azurerm" {
  features {}
  subscription_id = "00000000-0000-0000-0000-000000000000"
  metadata_host   = "localhost.localstack.cloud:4566"
}

resource "random_string" "suffix" {
  length  = 8
  upper   = false
  special = false
}

resource "azurerm_resource_group" "demo" {
  name     = "rg-nullstate-${random_string.suffix.result}"
  location = "westeurope"
}

resource "azurerm_storage_account" "demo" {
  name                             = "nullstate${random_string.suffix.result}"
  resource_group_name              = azurerm_resource_group.demo.name
  location                         = azurerm_resource_group.demo.location
  account_tier                     = "Standard"
  account_replication_type         = "LRS"
  allow_nested_items_to_be_public  = true
}

resource "azurerm_storage_container" "secrets" {
  name                  = "secrets"
  storage_account_id    = azurerm_storage_account.demo.id
  container_access_type = "container"
}

resource "azurerm_storage_blob" "evidence" {
  name                   = "evidence.txt"
  storage_account_name   = azurerm_storage_account.demo.name
  storage_container_name = azurerm_storage_container.secrets.name
  type                   = "Block"
  source_content         = "nullstate public Azure Blob evidence"
  content_type           = "text/plain"
}
