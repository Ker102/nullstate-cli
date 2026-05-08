import textwrap
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from nullstate.remediation import remediate_terraform_files


class RemediationTests(unittest.TestCase):
    def test_makes_public_container_private_and_disables_nested_public_items(self):
        with TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            main_tf = tmp / "main.tf"
            main_tf.write_text(
                textwrap.dedent(
                    """
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
                ).strip()
                + "\n",
                encoding="utf-8",
            )

            result = remediate_terraform_files(tmp)

            updated = main_tf.read_text(encoding="utf-8")
            self.assertTrue(result.changed)
            self.assertIn('container_access_type = "private"', updated)
            self.assertIn("allow_nested_items_to_be_public  = false", updated)
            self.assertIn('-  container_access_type = "container"', result.diff)
            self.assertIn('+  container_access_type = "private"', result.diff)

    def test_adds_missing_storage_account_public_block_setting(self):
        with TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            main_tf = tmp / "main.tf"
            main_tf.write_text(
                textwrap.dedent(
                    """
                    resource "azurerm_storage_account" "demo" {
                      name                     = "nullstatedemo"
                      resource_group_name      = azurerm_resource_group.demo.name
                      location                 = azurerm_resource_group.demo.location
                      account_tier             = "Standard"
                      account_replication_type = "LRS"
                    }
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )

            result = remediate_terraform_files(tmp)

            updated = main_tf.read_text(encoding="utf-8")
            self.assertTrue(result.changed)
            self.assertIn("allow_nested_items_to_be_public = false", updated)


if __name__ == "__main__":
    unittest.main()
