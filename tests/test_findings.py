import unittest

from nullstate.findings import find_public_blob_exposures


def plan_with_container(access_type="blob", allow_nested=True):
    return {
        "planned_values": {
            "root_module": {
                "resources": [
                    {
                        "address": "azurerm_storage_account.demo",
                        "type": "azurerm_storage_account",
                        "name": "demo",
                        "values": {
                            "name": "nullstatedemo",
                            "allow_nested_items_to_be_public": allow_nested,
                        },
                    },
                    {
                        "address": "azurerm_storage_container.secrets",
                        "type": "azurerm_storage_container",
                        "name": "secrets",
                        "values": {
                            "name": "secrets",
                            "storage_account_id": "/subscriptions/000/resourceGroups/rg/providers/Microsoft.Storage/storageAccounts/nullstatedemo",
                            "container_access_type": access_type,
                        },
                    },
                ]
            }
        },
        "configuration": {
            "root_module": {
                "resources": [
                    {
                        "address": "azurerm_storage_container.secrets",
                        "type": "azurerm_storage_container",
                        "name": "secrets",
                    }
                ]
            }
        },
    }


class FindingTests(unittest.TestCase):
    def test_detects_public_blob_container(self):
        findings = find_public_blob_exposures(plan_with_container("container", True))

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].resource_address, "azurerm_storage_container.secrets")
        self.assertEqual(findings[0].severity, "high")
        self.assertIn("container_access_type", findings[0].evidence)

    def test_ignores_private_container(self):
        findings = find_public_blob_exposures(plan_with_container("private", True))

        self.assertEqual(findings, [])

    def test_flags_public_container_even_when_storage_account_is_unknown(self):
        plan = plan_with_container("blob", None)
        plan["planned_values"]["root_module"]["resources"] = [
            resource
            for resource in plan["planned_values"]["root_module"]["resources"]
            if resource["type"] != "azurerm_storage_account"
        ]

        findings = find_public_blob_exposures(plan)

        self.assertEqual(len(findings), 1)
        self.assertIn("Storage account public nesting setting was not found", findings[0].evidence)


if __name__ == "__main__":
    unittest.main()
