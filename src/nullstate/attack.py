from __future__ import annotations

from pathlib import Path

from .findings import Finding


ATTACK_SCRIPTS = {
    "azure-public-blob": """\
from pathlib import Path

def main():
    # Demo exploit placeholder: in online mode this targets the LocalStack Azure blob endpoint.
    print("Attempting anonymous Azure Blob read against LocalStack endpoint")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
""",
    "aws-public-s3": """\
def main():
    print("Attempting anonymous S3 object read against LocalStack AWS endpoint")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
""",
    "k8s-privileged-pod": """\
def main():
    print("Checking whether the privileged pod can access host-mounted paths")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
""",
    "compose-exposed-admin": """\
def main():
    print("Checking public admin port exposure from the host network")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
""",
    "onprem-ssh-password": """\
def main():
    print("Checking SSH password and root login exposure in the on-prem baseline")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
""",
    "generic-plan-review": """\
def main():
    print("Reviewing public administrative ingress from exported plan data")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
""",
}

ATTACK_DETAILS = {
    "AZURE_STORAGE_PUBLIC_BLOB": "Anonymous read returned demo blob secret.txt from public container.",
    "AWS_S3_PUBLIC_ACCESS_BLOCK_DISABLED": "Anonymous S3 read hypothesis succeeded because public access block controls were disabled.",
    "K8S_PRIVILEGED_WORKLOAD": "Privileged pod could mount host paths in the local Kubernetes digital twin.",
    "COMPOSE_PUBLIC_ADMIN_PORT": "Admin service was reachable through a host port bound to 0.0.0.0.",
    "ONPREM_SSH_PASSWORD_LOGIN": "SSH baseline allowed password or root login in the on-prem digital twin.",
    "GENERIC_PUBLIC_ADMIN_INGRESS": "Plan-only attacker hypothesis found internet ingress to an administrative port.",
}


def write_attack_script(path: Path, scenario_name: str = "azure-public-blob") -> None:
    path.write_text(ATTACK_SCRIPTS.get(scenario_name, ATTACK_SCRIPTS["azure-public-blob"]), encoding="utf-8")


def simulate_attack(findings: list[Finding], stage: str) -> dict[str, str]:
    if stage == "before" and findings:
        return {"status": "success", "detail": ATTACK_DETAILS.get(findings[0].rule_id, findings[0].summary)}
    if stage == "before":
        return {"status": "blocked", "detail": "No exploitable scenario condition was found."}
    return {"status": "blocked", "detail": "Attack path denied after deterministic remediation."}
