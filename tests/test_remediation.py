import textwrap
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from nullstate.remediation import remediate_scenario_files, remediate_terraform_files


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

    def test_aws_remediation_removes_public_read_bucket_policy(self):
        with TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            main_tf = tmp / "main.tf"
            main_tf.write_text(
                textwrap.dedent(
                    """
                    resource "aws_s3_bucket_public_access_block" "public_logs" {
                      bucket                  = aws_s3_bucket.public_logs.id
                      block_public_acls       = false
                      block_public_policy     = false
                      ignore_public_acls      = false
                      restrict_public_buckets = false
                    }

                    resource "aws_s3_bucket_policy" "public_read" {
                      bucket = aws_s3_bucket.public_logs.id
                      policy = jsonencode({
                        Statement = [{
                          Principal = "*"
                          Action    = "s3:GetObject"
                          Resource  = "${aws_s3_bucket.public_logs.arn}/evidence.txt"
                        }]
                      })
                    }

                    resource "aws_s3_object" "evidence" {
                      bucket  = aws_s3_bucket.public_logs.id
                      key     = "evidence.txt"
                      content = "nullstate public S3 evidence"
                    }
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )

            result = remediate_scenario_files("aws-public-s3", tmp)

            updated = main_tf.read_text(encoding="utf-8")
            self.assertTrue(result.changed)
            self.assertIn("block_public_acls       = true", updated)
            self.assertNotIn('resource "aws_s3_bucket_policy" "public_read"', updated)
            self.assertNotIn('resource "aws_s3_object" "evidence"', updated)
            self.assertIn('-resource "aws_s3_bucket_policy" "public_read"', result.diff)
            self.assertIn('-resource "aws_s3_object" "evidence"', result.diff)


if __name__ == "__main__":
    unittest.main()
