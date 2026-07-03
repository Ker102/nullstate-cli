import json
import re
import unittest
from pathlib import Path


class GithubWorkflowTests(unittest.TestCase):
    def test_nullstate_sarif_workflow_exports_and_uploads_sarif(self):
        workflow = Path(".github/workflows/nullstate-sarif.yml")

        self.assertTrue(workflow.is_file(), "Expected the Nullstate SARIF workflow to exist.")
        text = workflow.read_text(encoding="utf-8")

        self.assertIn("python -m nullstate run", text)
        self.assertIn("examples/aws-public-s3", text)
        self.assertIn("--offline", text)
        self.assertIn("--mock-agents", text)
        self.assertIn("--ci", text)
        self.assertIn("--fail-on-severity none", text)
        self.assertIn("--runs-dir runs/ci", text)
        self.assertIn("python -m nullstate sarif", text)
        self.assertIn("--output artifacts/nullstate.sarif", text)
        self.assertIn("github/codeql-action/upload-sarif", text)
        self.assertIn("security-events: write", text)
        unpinned_action = re.compile(r"^\s*-\s*uses:\s*[^@\s]+@(?![0-9a-fA-F]{40}\b)", re.MULTILINE)
        self.assertNotRegex(text, unpinned_action)
        self.assertIn("persist-credentials: false", text)

    def test_enforcing_github_actions_template_preserves_evidence(self):
        template = Path("docs/templates/github-actions/nullstate-enforcing.yml")

        self.assertTrue(template.is_file(), "Expected an enforcing GitHub Actions template to exist.")
        text = template.read_text(encoding="utf-8")
        docs_text = Path("docs/ci-cd.md").read_text(encoding="utf-8")

        self.assertIn("continue-on-error: true", text)
        self.assertIn("python -m nullstate policy validate", text)
        self.assertIn("NULLSTATE_FAIL_ON_SEVERITY: high", text)
        self.assertIn('--ci --fail-on-severity "$NULLSTATE_FAIL_ON_SEVERITY"', text)
        self.assertIn("python -m nullstate policy-result", text)
        self.assertIn("python -m nullstate sarif", text)
        self.assertIn("python -m nullstate evidence-manifest", text)
        self.assertIn("python -m nullstate evidence-verify", text)
        self.assertIn("python -m nullstate bundle", text)
        self.assertIn("python -m nullstate upload --runs-dir runs/ci --dry-run", text)
        self.assertIn("github/codeql-action/upload-sarif", text)
        self.assertIn("actions/upload-artifact", text)
        self.assertIn("steps.nullstate_run.outcome == 'failure'", text)
        self.assertIn("docs/templates/github-actions/nullstate-enforcing.yml", docs_text)

    def test_release_workflow_generates_manifest_and_attestations(self):
        workflow = Path(".github/workflows/release.yml")

        self.assertTrue(workflow.is_file(), "Expected the release workflow to exist.")
        text = workflow.read_text(encoding="utf-8")

        self.assertIn("contents: write", text)
        self.assertIn("id-token: write", text)
        self.assertIn("attestations: write", text)
        self.assertIn("workflow_dispatch:", text)
        self.assertIn("dry_run:", text)
        self.assertIn("python -m build", text)
        self.assertIn("Smoke install release wheel", text)
        self.assertIn("python -m venv .smoke-venv", text)
        self.assertIn(".smoke-venv/bin/python -m pip install dist/*.whl", text)
        self.assertIn(".smoke-venv/bin/nullstate doctor --offline", text)
        self.assertIn("release-manifest.json", text)
        self.assertIn("sbom.spdx.json", text)
        self.assertIn("spdxVersion", text)
        self.assertIn("tomllib", text)
        self.assertIn("python -m venv .sbom-venv", text)
        self.assertIn(".sbom-venv/bin/python -m pip install dist/*.whl", text)
        self.assertIn("import importlib.metadata", text)
        self.assertIn('excluded_tools = {"pip", "setuptools", "wheel"}', text)
        self.assertIn('"versionInfo": distribution.version', text)
        self.assertIn("Validate release SBOM", text)
        self.assertIn('sbom_path = Path("dist/sbom.spdx.json")', text)
        self.assertIn('if sbom.get("spdxVersion") != "SPDX-2.3"', text)
        self.assertIn('required_package_fields = {"SPDXID", "name", "versionInfo"}', text)
        self.assertIn('forbidden_packages = {"pip", "setuptools", "wheel"}', text)
        self.assertIn('relationshipType") == "DESCRIBES"', text)
        self.assertIn("Validate SBOM with SPDX tools", text)
        self.assertIn(".sbom-venv/bin/python -m pip install spdx-tools==0.8.5", text)
        self.assertIn(".sbom-venv/bin/pyspdxtools -i dist/sbom.spdx.json", text)
        self.assertIn("relationships", text)
        self.assertIn('r"[<>=!~;\\[\\], ]"', text)
        self.assertIn("hashlib.sha256", text)
        self.assertIn("actions/attest@v4", text)
        self.assertIn("subject-path: dist/*", text)
        self.assertIn("Attest release SBOM", text)
        self.assertIn("sbom-path: dist/sbom.spdx.json", text)
        self.assertIn("Sign release artifacts", text)
        self.assertIn("sigstore/gh-action-sigstore-python@v3.4.0", text)
        self.assertIn("dist/*.whl", text)
        self.assertIn("dist/*.tar.gz", text)
        self.assertIn("dist/sbom.spdx.json", text)
        self.assertIn("dist/release-manifest.json", text)
        self.assertIn("release-signing-artifacts: false", text)
        self.assertIn("Validate release signatures", text)
        self.assertIn('signature_path = path.with_name(path.name + ".sigstore.json")', text)
        self.assertIn("Release dry-run summary", text)
        self.assertIn("github.event_name == 'workflow_dispatch'", text)
        self.assertIn("No GitHub release was created.", text)
        self.assertIn("if: github.event_name == 'push'", text)
        self.assertIn('gh release create "${GITHUB_REF_NAME}" dist/* --generate-notes', text)

    def test_release_docs_include_sbom_attestation_verification(self):
        docs_text = "\n".join(
            [
                Path("README.md").read_text(encoding="utf-8"),
                Path("docs/ci-cd.md").read_text(encoding="utf-8"),
                Path("docs/runbook.md").read_text(encoding="utf-8"),
            ]
        )

        self.assertIn(
            "gh attestation verify dist/nullstate-*.whl -R Ker102/nullstate-cli --predicate-type https://spdx.dev/Document/v2.3",
            docs_text,
        )
        self.assertIn("cosign verify-blob", docs_text)
        self.assertIn("https://github.com/Ker102/nullstate-cli/.github/workflows/release.yml@refs/tags/v0.1.0", docs_text)
        self.assertIn("https://token.actions.githubusercontent.com", docs_text)
        self.assertIn("First Tagged Release Checklist", docs_text)
        self.assertIn("gh workflow run Release --field dry_run=true", docs_text)
        self.assertIn("gh release view v0.1.0", docs_text)

    def test_release_install_smoke_script_checks_console_entrypoint(self):
        script = Path("scripts/release/install_smoke.py")
        pyproject = Path("pyproject.toml").read_text(encoding="utf-8")
        readme_text = Path("README.md").read_text(encoding="utf-8")

        self.assertTrue(script.is_file(), "Expected a local release install-smoke script.")
        text = script.read_text(encoding="utf-8")
        self.assertIn('"build"', pyproject)
        self.assertIn('"-m", "build"', text)
        self.assertIn("venv.EnvBuilder", text)
        self.assertIn('"doctor", "--offline"', text)
        self.assertIn("nullstate console command", text)
        self.assertIn("scripts/release/install_smoke.py", readme_text)

    def test_public_docs_point_to_current_prerelease(self):
        readme_text = Path("README.md").read_text(encoding="utf-8")

        self.assertIn("v0.1.0-alpha.2", readme_text)
        self.assertIn("git+https://github.com/Ker102/nullstate-cli.git@v0.1.0-alpha.2", readme_text)
        self.assertIn("Open-source readiness prerelease", readme_text)

    def test_issue_templates_collect_safe_repro_context(self):
        bug_template = Path(".github/ISSUE_TEMPLATE/bug_report.yml").read_text(encoding="utf-8")
        feature_template = Path(".github/ISSUE_TEMPLATE/feature_request.yml").read_text(encoding="utf-8")

        self.assertIn("Run ID or artifact context", bug_template)
        self.assertIn("Do not paste secrets", bug_template)
        self.assertIn("Security boundary", bug_template)
        self.assertIn("Open-source or paid-platform scope", feature_template)
        self.assertIn("User workflow", feature_template)

    def test_open_source_readiness_milestones_are_documented(self):
        readiness = Path("docs/open-source-readiness.md")

        self.assertTrue(readiness.is_file(), "Expected an open-source readiness milestone document.")
        text = readiness.read_text(encoding="utf-8")

        self.assertIn("Milestone 1: Alpha publication readiness", text)
        self.assertIn("Milestone 2: Stable local sandbox validation", text)
        self.assertIn("Milestone 3: Open-source stable CLI", text)
        self.assertIn("LocalStack Azure entitlement", text)
        self.assertIn("Azurite fallback", text)
        self.assertIn("[x] Run dependency audit and document any accepted risk.", text)

    def test_dependency_audit_status_is_documented(self):
        audit_doc = Path("docs/dependency-audit.md")
        readme_text = Path("README.md").read_text(encoding="utf-8")

        self.assertTrue(audit_doc.is_file(), "Expected dependency audit documentation.")
        text = audit_doc.read_text(encoding="utf-8")
        self.assertIn("python -m pip_audit . --skip-editable", text)
        self.assertIn("pip-audit 2.10.0", text)
        self.assertIn("No known vulnerabilities found", text)
        self.assertIn("No accepted vulnerable dependency risk is currently documented.", text)
        self.assertIn("docs/dependency-audit.md", readme_text)

    def test_first_ten_minutes_quickstart_is_documented(self):
        quickstart = Path("docs/quickstart-10-minutes.md")
        readme_text = Path("README.md").read_text(encoding="utf-8")

        self.assertTrue(quickstart.is_file(), "Expected a first-10-minutes quickstart.")
        text = quickstart.read_text(encoding="utf-8")

        self.assertIn("No Docker required", text)
        self.assertIn("python -m pip install -e", text)
        self.assertIn("nullstate doctor --offline", text)
        self.assertIn("nullstate run examples/aws-public-s3 --offline --mock-agents", text)
        self.assertIn("nullstate dashboard --open", text)
        self.assertIn("docs/quickstart-10-minutes.md", readme_text)

    def test_sample_run_artifact_is_present_and_scrubbed(self):
        sample_root = Path("examples/sample-runs")
        sample_runs = [path for path in sample_root.iterdir() if path.is_dir()]

        self.assertTrue(sample_runs, "Expected at least one sanitized sample run artifact.")
        sample_run = sample_runs[0]
        self.assertTrue(sample_run.joinpath("report.md").is_file())
        self.assertTrue(sample_run.joinpath("events.jsonl").is_file())
        self.assertTrue(sample_run.joinpath("run-bundle.json").is_file())
        self.assertTrue(sample_run.joinpath("dashboard.html").is_file())
        self.assertTrue(sample_run.joinpath("scrub-report.json").is_file())
        report = json.loads(sample_run.joinpath("scrub-report.json").read_text(encoding="utf-8"))
        self.assertEqual(report["source_run_dir"], "<redacted-source-run-dir>")
        self.assertEqual(report["scrubbed_run_dir"], "<redacted-scrubbed-run-dir>")
        bundle = json.loads(sample_run.joinpath("run-bundle.json").read_text(encoding="utf-8"))
        self.assertEqual(bundle["run"]["path"], ".")
        self.assertIn("dashboard.html", {artifact["path"] for artifact in bundle["artifacts"]})
        self.assertNotIn("run-bundle.json", {artifact["path"] for artifact in bundle["artifacts"]})
        combined_text = "\n".join(
            path.read_text(encoding="utf-8")
            for path in sample_run.rglob("*")
            if path.is_file() and path.suffix.lower() in {"", ".html", ".json", ".jsonl", ".md", ".patch", ".py", ".tf", ".txt"}
        )
        self.assertNotRegex(combined_text, r"C:\\Users\\")
        self.assertNotIn("LOCALSTACK_AUTH_TOKEN", combined_text)
        self.assertNotIn("NULLSTATE_LLM_API_KEY", combined_text)

    def test_case_study_records_alpha_status_without_overclaiming_azure(self):
        case_study = Path("docs/case-study.md").read_text(encoding="utf-8")

        self.assertIn("Open-source readiness status", case_study)
        self.assertIn("AWS LocalStack path is live-validated", case_study)
        self.assertIn("Azure Blob path is not yet live-validated", case_study)
        self.assertIn("LocalStack Azure Emulator entitlement", case_study)


if __name__ == "__main__":
    unittest.main()
