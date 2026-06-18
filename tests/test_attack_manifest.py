import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from nullstate.attack_manifest import ATTACK_MANIFEST_SCHEMA_ID, validate_attack_manifest, write_attack_manifest


class AttackManifestTests(unittest.TestCase):
    def test_writes_manifest_with_scenario_backend_target_and_resource_hints(self):
        with TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)
            workspace = root / "workspace"
            workspace.mkdir()
            (workspace / "main.tf").write_text(
                'resource "aws_s3_bucket" "public_logs" {\n'
                '  bucket_prefix = "nullstate-public-logs-"\n'
                "}\n"
                'resource "aws_s3_object" "evidence" {\n'
                '  key = "evidence.txt"\n'
                "}\n",
                encoding="utf-8",
            )
            manifest_path = root / "attack-manifest.json"

            manifest = write_attack_manifest(
                manifest_path,
                scenario_name="aws-public-s3",
                backend_name="localstack-aws",
                target_url="http://localhost.localstack.cloud:4566",
                workspace_dir=workspace,
            )

            self.assertEqual(manifest["$schema"], ATTACK_MANIFEST_SCHEMA_ID)
            self.assertEqual(manifest["schema_version"], 1)
            self.assertEqual(manifest["scenario"], "aws-public-s3")
            self.assertEqual(manifest["backend"], "localstack-aws")
            self.assertEqual(manifest["target_url"], "http://localhost.localstack.cloud:4566")
            self.assertEqual(manifest["resources"]["bucket_hint"], "nullstate-public-logs-")
            self.assertEqual(manifest["resources"]["object_key"], "evidence.txt")
            self.assertEqual(json.loads(manifest_path.read_text(encoding="utf-8")), manifest)

    def test_manifest_prefers_applied_terraform_state_resource_names(self):
        with TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)
            workspace = root / "workspace"
            workspace.mkdir()
            (workspace / "main.tf").write_text(
                'resource "aws_s3_bucket" "public_logs" {\n'
                '  bucket_prefix = "nullstate-public-logs-"\n'
                "}\n",
                encoding="utf-8",
            )
            (workspace / "terraform.tfstate").write_text(
                json.dumps(
                    {
                        "resources": [
                            {
                                "type": "aws_s3_bucket",
                                "name": "public_logs",
                                "instances": [{"attributes": {"bucket": "nullstate-public-logs-actual"}}],
                            },
                            {
                                "type": "aws_s3_object",
                                "name": "evidence",
                                "instances": [{"attributes": {"key": "evidence.txt"}}],
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )

            manifest = write_attack_manifest(
                root / "attack-manifest.json",
                scenario_name="aws-public-s3",
                backend_name="localstack-aws",
                target_url="http://localhost.localstack.cloud:4566",
                workspace_dir=workspace,
            )

            self.assertEqual(manifest["resources"]["bucket_name"], "nullstate-public-logs-actual")
            self.assertEqual(manifest["resources"]["bucket_hint"], "nullstate-public-logs-")
            self.assertEqual(manifest["resources"]["object_key"], "evidence.txt")

    def test_writes_azure_blob_manifest_with_state_resource_names(self):
        with TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)
            workspace = root / "workspace"
            workspace.mkdir()
            (workspace / "main.tf").write_text(
                'resource "azurerm_storage_account" "demo" {\n'
                '  name = "nullstate${random_string.suffix.result}"\n'
                "}\n"
                'resource "azurerm_storage_container" "secrets" {\n'
                '  name = "secrets"\n'
                "}\n"
                'resource "azurerm_storage_blob" "evidence" {\n'
                '  name = "evidence.txt"\n'
                "}\n",
                encoding="utf-8",
            )
            (workspace / "terraform.tfstate").write_text(
                json.dumps(
                    {
                        "resources": [
                            {
                                "type": "azurerm_storage_account",
                                "name": "demo",
                                "instances": [{"attributes": {"name": "nullstateactual"}}],
                            },
                            {
                                "type": "azurerm_storage_container",
                                "name": "secrets",
                                "instances": [{"attributes": {"name": "secrets"}}],
                            },
                            {
                                "type": "azurerm_storage_blob",
                                "name": "evidence",
                                "instances": [{"attributes": {"name": "evidence.txt"}}],
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )

            manifest = write_attack_manifest(
                root / "attack-manifest.json",
                scenario_name="azure-public-blob",
                backend_name="localstack-azure",
                target_url="http://localhost.localstack.cloud:4566",
                workspace_dir=workspace,
            )

            self.assertEqual(manifest["resources"]["storage_account_name"], "nullstateactual")
            self.assertEqual(manifest["resources"]["container_name"], "secrets")
            self.assertEqual(manifest["resources"]["blob_name"], "evidence.txt")

    def test_attack_manifest_validation_reports_contract_errors(self):
        errors = validate_attack_manifest({"schema_version": 1})

        self.assertIn("$schema must reference the nullstate attack-manifest schema", errors)
        self.assertIn("scenario is required", errors)
        self.assertIn("backend is required", errors)
        self.assertIn("target_url is required", errors)
        self.assertIn("resources must be an object", errors)

    def test_attack_manifest_schema_document_matches_generated_contract(self):
        schema_path = Path("docs/schemas/attack-manifest.schema.json")
        self.assertTrue(schema_path.is_file())
        schema = json.loads(schema_path.read_text(encoding="utf-8"))

        self.assertEqual(schema["$id"], ATTACK_MANIFEST_SCHEMA_ID)
        self.assertEqual(schema["properties"]["schema_version"]["const"], 1)
        self.assertIn("resources", schema["required"])


if __name__ == "__main__":
    unittest.main()
