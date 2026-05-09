import subprocess
import sys
import unittest

from nullstate.sandbox import get_backend, list_backends


class SandboxTests(unittest.TestCase):
    def test_lists_core_hackathon_backends(self):
        backend_names = {backend.name for backend in list_backends()}

        self.assertIn("localstack-azure", backend_names)
        self.assertIn("localstack-aws", backend_names)
        self.assertIn("kind-kubernetes", backend_names)
        self.assertIn("docker-compose", backend_names)
        self.assertIn("microvm-onprem", backend_names)
        self.assertIn("plan-only", backend_names)

    def test_localstack_azure_up_plan_uses_docker_and_auth_token(self):
        backend = get_backend("localstack-azure")
        commands = backend.up_commands()

        rendered = "\n".join(" ".join(command) for command in commands)
        self.assertIn("localstack/localstack-azure-alpha", rendered)
        self.assertIn("LOCALSTACK_AUTH_TOKEN", rendered)
        self.assertIn("4566:4566", rendered)
        self.assertIn("--name localstack-azure", rendered)
        self.assertIn("-d", rendered)

    def test_localstack_aws_up_plan_passes_auth_token(self):
        backend = get_backend("localstack-aws")
        commands = backend.up_commands()

        rendered = "\n".join(" ".join(command) for command in commands)
        self.assertIn("localstack/localstack", rendered)
        self.assertIn("LOCALSTACK_AUTH_TOKEN", rendered)
        self.assertIn("--name localstack", rendered)

    def test_plan_only_backend_has_no_external_runtime(self):
        backend = get_backend("plan-only")

        self.assertEqual(backend.requirements, [])
        self.assertEqual(backend.up_commands(), [])
        self.assertTrue(backend.available_without_runtime)

    def test_sandbox_list_cli_mentions_on_prem_and_localstack(self):
        completed = subprocess.run(
            [sys.executable, "-m", "nullstate", "sandbox", "list"],
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("localstack-azure", completed.stdout)
        self.assertIn("microvm-onprem", completed.stdout)

    def test_sandbox_up_dry_run_prints_commands_without_executing(self):
        completed = subprocess.run(
            [sys.executable, "-m", "nullstate", "sandbox", "up", "localstack-azure", "--dry-run"],
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("docker run", completed.stdout)
        self.assertIn("localstack/localstack-azure-alpha", completed.stdout)

    def test_sandbox_up_dry_run_accepts_env_file(self):
        completed = subprocess.run(
            [sys.executable, "-m", "nullstate", "sandbox", "up", "localstack-aws", "--dry-run", "--env-file", ".env.local"],
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("--env-file .env.local", completed.stdout)
        self.assertNotIn("-e LOCALSTACK_AUTH_TOKEN", completed.stdout)

    def test_localstack_down_plan_stops_named_containers(self):
        azure = get_backend("localstack-azure")
        aws = get_backend("localstack-aws")

        self.assertEqual(azure.down_commands(), [["docker", "rm", "-f", "localstack-azure"]])
        self.assertEqual(aws.down_commands(), [["docker", "rm", "-f", "localstack"]])

    def test_sandbox_status_cli_includes_runtime_probe_rows(self):
        completed = subprocess.run(
            [sys.executable, "-m", "nullstate", "sandbox", "status", "localstack-azure"],
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("Runtime docker", completed.stdout)
        self.assertIn("Runtime HTTP", completed.stdout)


if __name__ == "__main__":
    unittest.main()
