import os
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

    def test_localstack_aws_up_plan_accepts_alternate_container_name(self):
        backend = get_backend("localstack-aws")
        commands = backend.up_commands(container_name="localstack-20260510")

        rendered = "\n".join(" ".join(command) for command in commands)
        self.assertIn("--name localstack-20260510", rendered)
        self.assertNotIn("--name localstack ", rendered)

    def test_sandbox_container_name_changes_when_default_exists(self):
        from nullstate.cli import _resolve_sandbox_container_name

        backend = get_backend("localstack-aws")

        self.assertEqual(
            _resolve_sandbox_container_name(backend, container_exists=lambda _: False, suffix="20260510"),
            ("localstack", False),
        )
        self.assertEqual(
            _resolve_sandbox_container_name(backend, container_exists=lambda _: True, suffix="20260510"),
            ("localstack-20260510", True),
        )

    def test_sandbox_start_verification_accepts_running_container(self):
        from nullstate.cli import _verify_sandbox_container_started

        def fake_run(*args, **kwargs):
            return subprocess.CompletedProcess(args[0], 0, "true running 0\n", "")

        verified, detail = _verify_sandbox_container_started("localstack", runner=fake_run, sleep_seconds=0)

        self.assertTrue(verified)
        self.assertIn("running", detail)

    def test_sandbox_start_verification_rejects_exited_container(self):
        from nullstate.cli import _verify_sandbox_container_started

        def fake_run(*args, **kwargs):
            return subprocess.CompletedProcess(args[0], 0, "false exited 55\n", "")

        verified, detail = _verify_sandbox_container_started("localstack-azure", runner=fake_run, sleep_seconds=0)

        self.assertFalse(verified)
        self.assertIn("status=exited", detail)
        self.assertIn("exit_code=55", detail)

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

    def test_sandbox_env_file_defaults_to_local_env_files(self):
        from pathlib import Path
        from tempfile import TemporaryDirectory

        from nullstate.cli import _resolve_sandbox_env_file

        with TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)

            self.assertIsNone(_resolve_sandbox_env_file(None, [".env.local", ".env"], cwd=root))

            (root / ".env").write_text("LOCALSTACK_AUTH_TOKEN=test\n", encoding="utf-8")
            self.assertEqual(_resolve_sandbox_env_file(None, [".env.local", ".env"], cwd=root), root / ".env")

            (root / ".env.local").write_text("LOCALSTACK_AUTH_TOKEN=local\n", encoding="utf-8")
            self.assertEqual(_resolve_sandbox_env_file(None, [".env.local", ".env"], cwd=root), root / ".env.local")

            self.assertEqual(_resolve_sandbox_env_file(Path("custom.env"), [".env.local", ".env"], cwd=root), Path("custom.env"))

    def test_sandbox_up_dry_run_uses_default_env_file_when_present(self):
        from pathlib import Path
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)
            (root / ".env").write_text("LOCALSTACK_AUTH_TOKEN=test\n", encoding="utf-8")
            env = os.environ.copy()
            src_path = str(Path.cwd() / "src")
            env["PYTHONPATH"] = src_path + os.pathsep + env.get("PYTHONPATH", "")

            completed = subprocess.run(
                [sys.executable, "-m", "nullstate", "sandbox", "up", "localstack-aws", "--dry-run"],
                text=True,
                capture_output=True,
                check=False,
                cwd=root,
                env=env,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn("--env-file", completed.stdout)
            self.assertIn(".env", completed.stdout)
            self.assertIn("nullstate run examples/aws-public-s3", completed.stdout)

    def test_localstack_down_plan_stops_named_containers(self):
        azure = get_backend("localstack-azure")
        aws = get_backend("localstack-aws")

        self.assertEqual(azure.down_commands(), [["docker", "rm", "-f", "localstack-azure"]])
        self.assertEqual(aws.down_commands(), [["docker", "rm", "-f", "localstack"]])

    def test_localstack_down_plan_accepts_discovered_container_names(self):
        aws = get_backend("localstack-aws")

        self.assertEqual(
            aws.down_commands(container_names=["localstack", "localstack-20260510103849"]),
            [["docker", "rm", "-f", "localstack", "localstack-20260510103849"]],
        )

    def test_sandbox_down_discovers_backend_containers(self):
        from nullstate.cli import _resolve_sandbox_down_commands

        aws = get_backend("localstack-aws")

        commands, detail = _resolve_sandbox_down_commands(
            aws,
            container_lister=lambda _: ["localstack", "localstack-20260510103849"],
        )

        self.assertEqual(commands, [["docker", "rm", "-f", "localstack", "localstack-20260510103849"]])
        self.assertIn("localstack-20260510103849", detail)

    def test_sandbox_down_discovers_compose_style_localstack_container(self):
        from nullstate.cli import _list_sandbox_containers

        azure = get_backend("localstack-azure")

        def fake_run(*args, **kwargs):
            return subprocess.CompletedProcess(
                args[0],
                0,
                "localstack-azure\nnullstate-cli-localstack-azure-1\nunrelated-localstack\n",
                "",
            )

        original_run = subprocess.run
        try:
            subprocess.run = fake_run
            self.assertEqual(
                _list_sandbox_containers(azure),
                ["localstack-azure", "nullstate-cli-localstack-azure-1"],
            )
        finally:
            subprocess.run = original_run

    def test_sandbox_down_accepts_explicit_localstack_container_name(self):
        from nullstate.cli import _resolve_explicit_sandbox_container_down_commands

        self.assertEqual(
            _resolve_explicit_sandbox_container_down_commands("localstack-20260510103849"),
            [["docker", "rm", "-f", "localstack-20260510103849"]],
        )

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
