import unittest
from pathlib import Path
from unittest.mock import patch

from nullstate.terraform import CommandResult, apply_saved_plan


class TerraformTests(unittest.TestCase):
    def test_apply_saved_plan_uses_automation_flags(self):
        calls: list[list[str]] = []

        def fake_run(command: list[str], cwd: Path) -> CommandResult:
            calls.append(command)
            return CommandResult(command=command, returncode=0, stdout="applied", stderr="")

        with patch("nullstate.terraform.run_command", fake_run):
            results = apply_saved_plan(Path("workspace"))

        self.assertEqual(calls, [["terraform", "apply", "-auto-approve", "-input=false", "tfplan"]])
        self.assertEqual(results[0].stdout, "applied")

    def test_apply_saved_plan_raises_on_failure(self):
        def fake_run(command: list[str], cwd: Path) -> CommandResult:
            return CommandResult(command=command, returncode=1, stdout="", stderr="apply failed")

        with patch("nullstate.terraform.run_command", fake_run):
            with self.assertRaisesRegex(RuntimeError, "apply failed"):
                apply_saved_plan(Path("workspace"))


if __name__ == "__main__":
    unittest.main()
