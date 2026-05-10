from __future__ import annotations

from pathlib import Path

from .findings import Finding


ATTACK_SCRIPTS = {
    "azure-public-blob": """\
import argparse
import urllib.error
import urllib.request


def probe_target(target_url: str, stage: str) -> int:
    print(f"stage={stage} target={target_url}")
    if not target_url.startswith(("http://", "https://")):
        print("offline target selected; no network request performed")
        return 0
    health_url = target_url.rstrip("/") + "/_localstack/health"
    try:
        with urllib.request.urlopen(health_url, timeout=5) as response:
            print(f"health_url={health_url} status={response.status}")
            return 0 if response.status < 500 else 2
    except urllib.error.URLError as error:
        print(f"health_url={health_url} error={error}")
        return 2


def main():
    print("Attempting anonymous Azure Blob read against LocalStack endpoint")
    parser = argparse.ArgumentParser()
    parser.add_argument("--target-url", required=True)
    parser.add_argument("--stage", required=True, choices=["before", "after"])
    args = parser.parse_args()
    return probe_target(args.target_url, args.stage)

if __name__ == "__main__":
    raise SystemExit(main())
""",
    "aws-public-s3": """\
import argparse
import urllib.error
import urllib.request


def probe_target(target_url: str, stage: str) -> int:
    print(f"stage={stage} target={target_url}")
    if not target_url.startswith(("http://", "https://")):
        print("offline target selected; no network request performed")
        return 0
    health_url = target_url.rstrip("/") + "/_localstack/health"
    try:
        with urllib.request.urlopen(health_url, timeout=5) as response:
            print(f"health_url={health_url} status={response.status}")
            return 0 if response.status < 500 else 2
    except urllib.error.URLError as error:
        print(f"health_url={health_url} error={error}")
        return 2


def main():
    print("Attempting anonymous S3 object read against LocalStack AWS endpoint")
    parser = argparse.ArgumentParser()
    parser.add_argument("--target-url", required=True)
    parser.add_argument("--stage", required=True, choices=["before", "after"])
    args = parser.parse_args()
    return probe_target(args.target_url, args.stage)

if __name__ == "__main__":
    raise SystemExit(main())
""",
    "k8s-privileged-pod": """\
import argparse


def main():
    print("Checking whether the privileged pod can access host-mounted paths")
    parser = argparse.ArgumentParser()
    parser.add_argument("--target-url", required=True)
    parser.add_argument("--stage", required=True, choices=["before", "after"])
    parser.parse_args()
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
""",
    "compose-exposed-admin": """\
import argparse


def main():
    print("Checking public admin port exposure from the host network")
    parser = argparse.ArgumentParser()
    parser.add_argument("--target-url", required=True)
    parser.add_argument("--stage", required=True, choices=["before", "after"])
    parser.parse_args()
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
""",
    "onprem-ssh-password": """\
import argparse


def main():
    print("Checking SSH password and root login exposure in the on-prem baseline")
    parser = argparse.ArgumentParser()
    parser.add_argument("--target-url", required=True)
    parser.add_argument("--stage", required=True, choices=["before", "after"])
    parser.parse_args()
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
""",
    "generic-plan-review": """\
import argparse


def main():
    print("Reviewing public administrative ingress from exported plan data")
    parser = argparse.ArgumentParser()
    parser.add_argument("--target-url", required=True)
    parser.add_argument("--stage", required=True, choices=["before", "after"])
    parser.parse_args()
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
