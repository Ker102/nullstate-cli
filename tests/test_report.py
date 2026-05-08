import unittest

from nullstate.findings import Finding
from nullstate.report import render_report


class ReportTests(unittest.TestCase):
    def test_report_includes_before_after_evidence_and_patch(self):
        report = render_report(
            run_id="20260507-120000",
            terraform_dir="examples/azure-public-blob",
            findings=[
                Finding(
                    rule_id="AZURE_STORAGE_PUBLIC_BLOB",
                    severity="high",
                    resource_address="azurerm_storage_container.secrets",
                    summary="Azure Blob container allows anonymous reads.",
                    evidence="container_access_type is container",
                    remediation="Set container_access_type to private.",
                )
            ],
            before_attack={"status": "success", "detail": "Anonymous read returned secret.txt"},
            after_attack={"status": "blocked", "detail": "Anonymous read denied"},
            patch_diff="--- a/main.tf\n+++ b/main.tf\n",
            model_notes="offline mock blue team",
        )

        self.assertIn("# nullstate Run Report", report)
        self.assertIn("Azure Blob container allows anonymous reads.", report)
        self.assertIn("Anonymous read returned secret.txt", report)
        self.assertIn("Anonymous read denied", report)
        self.assertIn("offline mock blue team", report)


if __name__ == "__main__":
    unittest.main()
