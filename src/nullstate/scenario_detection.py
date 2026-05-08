from __future__ import annotations

import json
from pathlib import Path

from .scenarios import Scenario, get_scenario


def infer_scenario(iac_dir: Path) -> Scenario | None:
    text_by_name = _read_iac_files(iac_dir)
    combined = "\n".join(text_by_name.values())

    if _looks_like_azure_public_blob(combined):
        return get_scenario("azure-public-blob")
    if _looks_like_aws_public_s3(combined):
        return get_scenario("aws-public-s3")
    if _looks_like_k8s_privileged_pod(combined):
        return get_scenario("k8s-privileged-pod")
    if _looks_like_compose_exposed_admin(text_by_name):
        return get_scenario("compose-exposed-admin")
    if _looks_like_onprem_ssh_password(combined):
        return get_scenario("onprem-ssh-password")
    if _looks_like_generic_plan_review(iac_dir):
        return get_scenario("generic-plan-review")
    return None


def _read_iac_files(iac_dir: Path) -> dict[str, str]:
    extensions = {".tf", ".tf.json", ".yaml", ".yml", ".json", ".cfg", ".conf"}
    result: dict[str, str] = {}
    for path in sorted(item for item in iac_dir.iterdir() if item.is_file()):
        if path.suffix not in extensions and not path.name.endswith(".tf.json"):
            continue
        result[path.name] = path.read_text(encoding="utf-8", errors="ignore")
    return result


def _looks_like_azure_public_blob(text: str) -> bool:
    return "azurerm_storage_container" in text and "container_access_type" in text


def _looks_like_aws_public_s3(text: str) -> bool:
    return "aws_s3_bucket_public_access_block" in text or "aws_s3_bucket" in text


def _looks_like_k8s_privileged_pod(text: str) -> bool:
    return ("apiVersion:" in text and "kind:" in text and "privileged: true" in text) or "hostPath:" in text


def _looks_like_compose_exposed_admin(text_by_name: dict[str, str]) -> bool:
    for name, text in text_by_name.items():
        if name in {"compose.yaml", "compose.yml", "docker-compose.yaml", "docker-compose.yml"} and "services:" in text:
            return True
    return False


def _looks_like_onprem_ssh_password(text: str) -> bool:
    return "PasswordAuthentication yes" in text or "PermitRootLogin yes" in text


def _looks_like_generic_plan_review(iac_dir: Path) -> bool:
    plan_path = iac_dir / "tfplan.json"
    if not plan_path.exists():
        return False
    try:
        payload = json.loads(plan_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    return "planned_values" in payload
