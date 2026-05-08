from __future__ import annotations

from pathlib import Path


DEMO_MAIN_TF = """\
terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "=4.14.0"
    }
  }
}

provider "azurerm" {
  features {}
  subscription_id = "00000000-0000-0000-0000-000000000000"
  metadata_host   = "localhost.localstack.cloud:4566"
}

resource "azurerm_resource_group" "demo" {
  name     = "rg-nullstate-demo"
  location = "westeurope"
}

resource "azurerm_storage_account" "demo" {
  name                             = "nullstatedemo"
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
"""


DEMO_README = """\
# nullstate Azure Public Blob Demo

This fixture intentionally exposes an Azure Blob container for anonymous reads.
Use it with:

```powershell
nullstate run . --offline
```

For the live LocalStack Azure demo, start LocalStack for Azure first and omit `--offline`.
"""


def create_demo(name: str, output: Path) -> None:
    if name != "azure-public-blob":
        raise ValueError("Only the azure-public-blob demo is available in v1.")
    output.mkdir(parents=True, exist_ok=True)
    (output / "main.tf").write_text(DEMO_MAIN_TF, encoding="utf-8")
    (output / "README.md").write_text(DEMO_README, encoding="utf-8")
