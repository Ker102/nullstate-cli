import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from nullstate.demo import create_demo
from nullstate.scenario_detection import infer_scenario


class ScenarioDetectionTests(unittest.TestCase):
    def test_infers_scenario_from_demo_iac_files(self):
        expectations = {
            "azure-public-blob": "azure-public-blob",
            "aws-public-s3": "aws-public-s3",
            "k8s-privileged-pod": "k8s-privileged-pod",
            "compose-exposed-admin": "compose-exposed-admin",
            "onprem-ssh-password": "onprem-ssh-password",
            "generic-plan-review": "generic-plan-review",
        }

        with TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)
            for demo_name, expected in expectations.items():
                demo_dir = root / demo_name
                create_demo(demo_name, demo_dir)

                inferred = infer_scenario(demo_dir)

                self.assertEqual(inferred.name, expected)

    def test_returns_none_when_iac_shape_is_unknown(self):
        with TemporaryDirectory() as raw_tmp:
            unknown_dir = Path(raw_tmp)
            (unknown_dir / "README.md").write_text("no IaC here", encoding="utf-8")

            self.assertIsNone(infer_scenario(unknown_dir))


if __name__ == "__main__":
    unittest.main()
