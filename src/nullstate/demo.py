from __future__ import annotations

from pathlib import Path

from .scenarios import get_scenario


AZURE_PUBLIC_BLOB_MAIN_TF = """\
terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "=4.14.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

provider "azurerm" {
  features {}
  subscription_id = "00000000-0000-0000-0000-000000000000"
  metadata_host   = "localhost.localstack.cloud:4566"
}

resource "random_string" "suffix" {
  length  = 8
  upper   = false
  special = false
}

resource "azurerm_resource_group" "demo" {
  name     = "rg-nullstate-${random_string.suffix.result}"
  location = "westeurope"
}

resource "azurerm_storage_account" "demo" {
  name                             = "nullstate${random_string.suffix.result}"
  resource_group_name              = azurerm_resource_group.demo.name
  location                         = azurerm_resource_group.demo.location
  account_tier                     = "Standard"
  account_replication_type         = "LRS"
  allow_nested_items_to_be_public  = true
}

resource "azurerm_storage_container" "secrets" {
  name                  = "secrets"
  storage_account_id    = azurerm_storage_account.demo.id
  container_access_type = "container"
}
"""


AZURE_PUBLIC_BLOB_README = """\
# nullstate Azure Public Blob Demo

This fixture intentionally exposes an Azure Blob container for anonymous reads.
Use it with:

```powershell
nullstate run . --offline
```

For the live LocalStack Azure demo, start LocalStack for Azure first and omit `--offline`.
"""

AWS_PUBLIC_S3_MAIN_TF = """\
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region                      = "us-east-1"
  access_key                  = "test"
  secret_key                  = "test"
  s3_use_path_style           = true
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true

  endpoints {
    s3 = "http://s3.localhost.localstack.cloud:4566"
  }
}

resource "aws_s3_bucket" "public_logs" {
  bucket_prefix = "nullstate-public-logs-"
}

resource "aws_s3_bucket_public_access_block" "public_logs" {
  bucket                  = aws_s3_bucket.public_logs.id
  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}
"""

K8S_PRIVILEGED_POD_YAML = """\
apiVersion: v1
kind: Pod
metadata:
  name: nullstate-privileged-pod
spec:
  containers:
    - name: shell
      image: alpine:latest
      command: ["sleep", "3600"]
      securityContext:
        privileged: true
      volumeMounts:
        - name: host-root
          mountPath: /host
  volumes:
    - name: host-root
      hostPath:
        path: /
"""

COMPOSE_EXPOSED_ADMIN_YAML = """\
services:
  admin:
    image: nginx:alpine
    ports:
      - "0.0.0.0:8080:80"
"""

ONPREM_ANSIBLE_PLAYBOOK = """\
- name: Intentionally weak on-prem SSH baseline
  hosts: all
  become: true
  tasks:
    - name: Enable password authentication
      lineinfile:
        path: /etc/ssh/sshd_config
        regexp: '^PasswordAuthentication'
        line: 'PasswordAuthentication yes'
    - name: Permit root login
      lineinfile:
        path: /etc/ssh/sshd_config
        regexp: '^PermitRootLogin'
        line: 'PermitRootLogin yes'
"""

GENERIC_PLAN_REVIEW_JSON = """\
{
  "format_version": "1.2",
  "terraform_version": "1.9.0",
  "planned_values": {
    "root_module": {
      "resources": [
        {
          "address": "example_firewall_rule.admin",
          "type": "example_firewall_rule",
          "name": "admin",
          "values": {
            "name": "admin-ssh",
            "source_ranges": ["0.0.0.0/0"],
            "destination_port": 22
          }
        }
      ]
    }
  }
}
"""


README_BY_SCENARIO = {
    "azure-public-blob": AZURE_PUBLIC_BLOB_README,
    "aws-public-s3": "# nullstate AWS Public S3 Demo\n\nOffline Terraform AWS scenario for LocalStack AWS public access review.\n",
    "k8s-privileged-pod": "# nullstate Kubernetes Privileged Pod Demo\n\nOffline Kubernetes scenario for kind privileged workload review.\n",
    "compose-exposed-admin": "# nullstate Docker Compose Exposed Admin Demo\n\nOffline digital-twin scenario for Docker Compose admin exposure review.\n",
    "onprem-ssh-password": "# nullstate On-Prem SSH Password Demo\n\nOffline digital-twin scenario for Ansible or VM SSH baseline review.\n",
    "generic-plan-review": (
        "# nullstate Generic Plan Review Demo\n\n"
        "Plan-only scenario for unsupported IaC providers with public administrative ingress.\n"
    ),
}


def create_demo(name: str, output: Path) -> None:
    scenario = get_scenario(name)
    output.mkdir(parents=True, exist_ok=True)
    if scenario.name == "azure-public-blob":
        (output / "main.tf").write_text(AZURE_PUBLIC_BLOB_MAIN_TF, encoding="utf-8")
    elif scenario.name == "aws-public-s3":
        (output / "main.tf").write_text(AWS_PUBLIC_S3_MAIN_TF, encoding="utf-8")
    elif scenario.name == "k8s-privileged-pod":
        (output / "pod.yaml").write_text(K8S_PRIVILEGED_POD_YAML, encoding="utf-8")
    elif scenario.name == "compose-exposed-admin":
        (output / "compose.yaml").write_text(COMPOSE_EXPOSED_ADMIN_YAML, encoding="utf-8")
    elif scenario.name == "onprem-ssh-password":
        (output / "playbook.yml").write_text(ONPREM_ANSIBLE_PLAYBOOK, encoding="utf-8")
    elif scenario.name == "generic-plan-review":
        (output / "tfplan.json").write_text(GENERIC_PLAN_REVIEW_JSON, encoding="utf-8")
    (output / "README.md").write_text(README_BY_SCENARIO[scenario.name], encoding="utf-8")
