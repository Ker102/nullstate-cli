import json
import subprocess
import sys
import unittest
from pathlib import Path

from nullstate.cloud_context import (
    CLOUD_CONTEXT_SCHEMA_ID,
    build_context_summary,
    load_cloud_context,
    validate_cloud_context,
)


EXAMPLE_CONTEXT = Path("examples/cloud-context/aws-readonly-context.json")


class CloudContextTests(unittest.TestCase):
    def test_loads_valid_cloud_context_manifest(self):
        context = load_cloud_context(EXAMPLE_CONTEXT)

        self.assertEqual(context["$schema"], CLOUD_CONTEXT_SCHEMA_ID)
        self.assertEqual(context["schema_version"], 1)
        self.assertEqual(context["scope"]["mode"], "read-only")
        self.assertEqual(validate_cloud_context(context), [])

    def test_context_validation_reports_missing_required_fields(self):
        errors = validate_cloud_context({"schema_version": 1})

        self.assertIn("$schema must reference the nullstate cloud-context schema", errors)
        self.assertIn("scope.mode must be read-only", errors)
        self.assertIn("providers must include at least one provider context", errors)

    def test_context_summary_counts_providers_identities_and_exposure(self):
        context = {
            "$schema": CLOUD_CONTEXT_SCHEMA_ID,
            "schema_version": 1,
            "scope": {"mode": "read-only", "source": "fixture"},
            "providers": [
                {
                    "name": "aws",
                    "accounts": [{"id": "111122223333", "name": "prod"}],
                    "identities": [
                        {"id": "arn:aws:iam::111122223333:role/github-actions", "type": "ci-workload"},
                        {"id": "arn:aws:iam::111122223333:role/app", "type": "workload"},
                    ],
                    "resources": [
                        {
                            "id": "s3://customer-prod-support-cases",
                            "type": "storage",
                            "public": True,
                            "data_classification": "confidential",
                        },
                        {
                            "id": "arn:aws:lambda:eu-west-1:111122223333:function:processor",
                            "type": "compute",
                            "public": False,
                            "data_classification": "internal",
                        },
                    ],
                }
            ],
        }

        summary = build_context_summary(context)

        self.assertEqual(summary["provider_count"], 1)
        self.assertEqual(summary["account_count"], 1)
        self.assertEqual(summary["identity_count"], 2)
        self.assertEqual(summary["resource_count"], 2)
        self.assertEqual(summary["public_resource_count"], 1)
        self.assertEqual(summary["sensitive_resource_count"], 1)
        self.assertIn("aws", summary["providers"])

    def test_cloud_context_schema_document_matches_contract(self):
        schema_path = Path("docs/schemas/cloud-context.schema.json")
        self.assertTrue(schema_path.is_file())
        schema = json.loads(schema_path.read_text(encoding="utf-8"))

        self.assertEqual(schema["$id"], CLOUD_CONTEXT_SCHEMA_ID)
        self.assertEqual(schema["properties"]["schema_version"]["const"], 1)
        self.assertIn("providers", schema["required"])

    def test_context_summary_cli_prints_json(self):
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "nullstate",
                "context",
                "summary",
                str(EXAMPLE_CONTEXT),
                "--json",
            ],
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["provider_count"], 1)
        self.assertEqual(payload["providers"], ["aws"])


if __name__ == "__main__":
    unittest.main()
