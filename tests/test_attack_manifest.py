import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from nullstate.attack_manifest import write_attack_manifest


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


if __name__ == "__main__":
    unittest.main()
