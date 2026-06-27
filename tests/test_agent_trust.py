import json
import unittest
from datetime import UTC, datetime
from pathlib import Path

from nullstate.agent_trust import (
    AGENT_MANIFEST_SCHEMA_ID,
    build_blast_radius_report,
    build_posture_report,
    load_agent_manifest,
    validate_agent_manifest,
)


EXAMPLE_MANIFEST = Path("examples/agent-trust/external-agent-manifest.json")


class AgentTrustTests(unittest.TestCase):
    def test_loads_valid_external_agent_manifest(self):
        manifest = load_agent_manifest(EXAMPLE_MANIFEST)

        self.assertEqual(manifest["$schema"], AGENT_MANIFEST_SCHEMA_ID)
        self.assertEqual(manifest["schema_version"], 1)
        self.assertEqual(manifest["agent"]["id"], "vendor-agent://ticket-triage")
        self.assertEqual(validate_agent_manifest(manifest), [])

    def test_manifest_validation_reports_missing_required_fields(self):
        errors = validate_agent_manifest({"schema_version": 1})

        self.assertIn("$schema must reference the nullstate external-agent-manifest schema", errors)
        self.assertIn("agent.id is required", errors)
        self.assertIn("runtime.environment is required", errors)
        self.assertIn("identities must include at least one identity", errors)
        self.assertIn("posture_evidence must include at least one evidence claim", errors)
        self.assertIn("reachable_resources must be a list", errors)

    def test_unknown_evidence_prevents_passing_posture(self):
        manifest = _valid_manifest()
        manifest["posture_evidence"][0]["evidence_class"] = "unknown"
        manifest["posture_evidence"][0]["status"] = "unknown"

        report = build_posture_report(manifest, now=datetime(2026, 6, 27, tzinfo=UTC))

        self.assertEqual(report["status"], "needs-review")
        self.assertFalse(report["passed"])
        self.assertIn("artifact_integrity", report["unknown_claims"])
        self.assertIn("unknown evidence", report["findings"][0]["detail"])

    def test_stale_evidence_prevents_passing_posture(self):
        manifest = _valid_manifest()
        manifest["posture_evidence"][0]["observed_at"] = "2026-06-01T00:00:00+00:00"
        manifest["posture_evidence"][0]["expires_at"] = "2026-06-02T00:00:00+00:00"

        report = build_posture_report(manifest, now=datetime(2026, 6, 27, tzinfo=UTC))

        self.assertEqual(report["status"], "fail")
        self.assertFalse(report["passed"])
        self.assertIn("artifact_integrity", report["stale_claims"])
        self.assertIn("expired", report["findings"][0]["detail"])

    def test_blast_radius_includes_agent_and_delegated_user_permissions(self):
        manifest = _valid_manifest()

        report = build_blast_radius_report(manifest)

        self.assertEqual(report["agent_id"], "vendor-agent://ticket-triage")
        self.assertEqual(report["identity_count"], 2)
        self.assertIn("agent", report["identity_types"])
        self.assertIn("delegated-user", report["identity_types"])
        self.assertEqual(report["sensitive_resource_count"], 1)
        self.assertIn("s3://customer-prod-support-cases", report["sensitive_resources"])
        self.assertIn("iam:PassRole", report["high_risk_actions"])
        self.assertIn("read_sensitive_data", report["attack_paths"])

    def test_schema_document_matches_manifest_contract(self):
        schema_path = Path("docs/schemas/external-agent-manifest.schema.json")
        self.assertTrue(schema_path.is_file())
        schema = json.loads(schema_path.read_text(encoding="utf-8"))

        self.assertEqual(schema["$id"], AGENT_MANIFEST_SCHEMA_ID)
        self.assertEqual(schema["properties"]["schema_version"]["const"], 1)
        self.assertIn("posture_evidence", schema["required"])


def _valid_manifest() -> dict:
    return {
        "$schema": AGENT_MANIFEST_SCHEMA_ID,
        "schema_version": 1,
        "agent": {
            "id": "vendor-agent://ticket-triage",
            "name": "Ticket triage agent",
            "owner": "support-platform",
        },
        "runtime": {
            "environment": "external-saas",
            "provider": "example-vendor",
            "region": "eu-west-1",
        },
        "identities": [
            {
                "id": "arn:aws:iam::111122223333:role/nullstate-agent",
                "type": "agent",
                "provider": "aws",
                "permissions": ["s3:GetObject", "iam:PassRole"],
            },
            {
                "id": "entra://user/support-admin@example.com",
                "type": "delegated-user",
                "provider": "azure",
                "permissions": ["Microsoft.Storage/storageAccounts/blobServices/containers/read"],
            },
        ],
        "tools": [
            {
                "id": "tool://support-case-reader",
                "type": "api",
                "target": "s3://customer-prod-support-cases",
            }
        ],
        "posture_evidence": [
            {
                "claim": "artifact_integrity",
                "status": "pass",
                "evidence_class": "cryptographically-verified",
                "observed_at": "2026-06-27T10:00:00+00:00",
                "expires_at": "2026-06-28T10:00:00+00:00",
                "source": "slsa-provenance",
            }
        ],
        "reachable_resources": [
            {
                "id": "s3://customer-prod-support-cases",
                "provider": "aws",
                "data_classification": "confidential",
                "actions": ["s3:GetObject"],
            },
            {
                "id": "arn:aws:iam::111122223333:role/deploy-admin",
                "provider": "aws",
                "data_classification": "privileged-control-plane",
                "actions": ["iam:PassRole"],
            },
        ],
    }


if __name__ == "__main__":
    unittest.main()
