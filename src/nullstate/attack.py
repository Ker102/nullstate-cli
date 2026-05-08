from __future__ import annotations

from pathlib import Path

from .findings import Finding


ATTACK_SCRIPT = """\
from pathlib import Path

def main():
    # Demo exploit placeholder: in online mode this targets the LocalStack Azure blob endpoint.
    print("Attempting anonymous Azure Blob read against LocalStack endpoint")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
"""


def write_attack_script(path: Path) -> None:
    path.write_text(ATTACK_SCRIPT, encoding="utf-8")


def simulate_attack(findings: list[Finding], stage: str) -> dict[str, str]:
    if stage == "before" and findings:
        return {"status": "success", "detail": "Anonymous read returned demo blob secret.txt from public container."}
    if stage == "before":
        return {"status": "blocked", "detail": "No public blob container was available to read."}
    return {"status": "blocked", "detail": "Anonymous read denied after Terraform remediation."}
