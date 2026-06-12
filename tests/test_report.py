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
            remediation_metadata={
                "ruleset_version": "2026.06.1",
                "rules_applied": ["AZURE_STORAGE_PUBLIC_BLOB_PRIVATE_ACCESS"],
                "changed_files": ["workspace/main.tf"],
            },
            runtime_evidence={
                "before": {
                    "command": ["python", "attack.py", "--stage", "before"],
                    "returncode": 0,
                    "target_url": "http://localhost.localstack.cloud:4566",
                    "stdout": "candidate_url=http://example/bucket/evidence.txt\nstatus=200\n",
                },
                "after": {
                    "command": ["python", "attack.py", "--stage", "after"],
                    "returncode": 2,
                    "target_url": "http://localhost.localstack.cloud:4566",
                    "stdout": "status=403\nruntime_exploit_observed=false\n",
                },
            },
        )

        self.assertIn("# nullstate Run Report", report)
        self.assertIn("Azure Blob container allows anonymous reads.", report)
        self.assertIn("Anonymous read returned secret.txt", report)
        self.assertIn("Anonymous read denied", report)
        self.assertIn("offline mock blue team", report)
        self.assertIn("## Remediation Metadata", report)
        self.assertIn("Ruleset version: `2026.06.1`", report)
        self.assertIn("AZURE_STORAGE_PUBLIC_BLOB_PRIVATE_ACCESS", report)
        self.assertIn("## Runtime Command Evidence", report)
        self.assertIn("Classification: `runtime evidence unavailable`", report)
        self.assertIn("Classification: `runtime probe did not observe exploit`", report)
        self.assertIn("candidate_url=http://example/bucket/evidence.txt", report)
        self.assertIn("runtime_exploit_observed=false", report)

    def test_report_classifies_observed_runtime_exploit(self):
        report = render_report(
            run_id="20260507-120000",
            terraform_dir="examples/aws-public-s3",
            findings=[],
            before_attack={"status": "success", "detail": "tool observed access"},
            after_attack={"status": "blocked", "detail": "blocked"},
            patch_diff="",
            model_notes="offline mock blue team",
            runtime_evidence={
                "before": {
                    "command": ["python", "attack.py", "--stage", "before"],
                    "returncode": 0,
                    "target_url": "http://localhost.localstack.cloud:4566",
                    "stdout": "status=200\nruntime_exploit_observed=true\n",
                },
                "after": {
                    "command": ["python", "attack.py", "--stage", "after"],
                    "returncode": 0,
                    "target_url": "offline://aws-public-s3",
                    "stdout": "offline target selected; runtime blob probe not performed\n",
                },
            },
        )

        self.assertIn("Classification: `runtime exploit observed`", report)
        self.assertIn("Classification: `offline deterministic simulation`", report)


if __name__ == "__main__":
    unittest.main()
