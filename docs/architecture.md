# nullstate Architecture

## Goal

Ship a repeatable purple-team workflow that begins with infrastructure-as-code and evolves toward correlation with observed AWS and Azure environments, without making real-cloud exploitation the default.

## Pipeline

```mermaid
flowchart LR
    A[Terraform / IaC directory] --> B[Plan JSON or static parser]
    B --> C[Deterministic exposure detector]
    C --> S[Sandbox adapter]
    S --> D[Red-team agent instructions]
    D --> E[Constrained attack.py runner]
    E --> F[Exploit evidence]
    F --> G[Blue-team agent instructions]
    G --> H[Deterministic remediation]
    H --> I[Validation attack]
    I --> J[Run report and metrics]
```

## Design Choices

- The deterministic detector is the source of truth for demo reliability.
- IaC describes intended configuration; future read-only AWS and Azure discovery supplies deployed state and drift.
- The long-term analysis substrate is a normalized environment graph spanning resources, network reachability, identities, privileges, services, and data impact.
- Attack paths are evaluated from explicit identities such as anonymous users, developers, CI workloads, compromised compute identities, AWS roles, and Azure managed identities.
- Disposable validation environments should reconstruct the smallest relevant attack path rather than clone an entire account or subscription.
- The red/blue agents receive internal role instructions and scenario evidence; users do not need to prompt the model manually.
- `run` defaults to `--scenario auto` and `--target auto`; explicit values remain available for demos and tests.
- Offline mode uses a static Terraform parser so demos still work without LocalStack, Terraform, or GPUs.
- Online mode follows Terraform automation commands: `init`, `plan -out=tfplan`, and `show -json tfplan`.
- Sandbox backends are explicit adapters: executable, digital twin, or plan-only.
- The red tool runner executes only generated run-directory `attack.py` scripts and logs command evidence into `events.jsonl`.

See [Product and validation model](product-validation-model.md) for production discovery, identity-aware attack analysis, exposed-data impact, fidelity levels, and CI trigger design.

## Sandbox adapters

| Backend | Mode | Target |
|---|---|---|
| `localstack-azure` | executable | Terraform AzureRM |
| `localstack-aws` | executable | Terraform AWS |
| `kind-kubernetes` | executable | Kubernetes YAML, Helm, Kustomize |
| `docker-compose` | digital twin | Docker Compose and app stacks |
| `microvm-onprem` | digital twin | on-prem Linux/VM/network-style IaC |
| `plan-only` | plan-only | any IaC with parser/exported plan |

## On-prem sandboxing model

On-prem infrastructure usually cannot be emulated by one universal cloud emulator. nullstate chooses the best available execution level:

- executable sandbox when a disposable runtime exists
- digital twin sandbox when the topology can be mapped to local containers or VMs
- plan-only analysis when execution would be unsafe or unsupported

## Current Rule

`AZURE_STORAGE_PUBLIC_BLOB` flags `azurerm_storage_container` resources where `container_access_type` is `blob` or `container`.

The remediation sets:

```hcl
container_access_type = "private"
allow_nested_items_to_be_public = false
```

## Scenario roadmap

| Scenario | Target | Sandbox | Execution status |
|---|---|---|---|
| `azure-public-blob` | Terraform AzureRM | LocalStack Azure or future Azurite fallback | manifest-backed/offline demo available; live LocalStack Azure validation pending emulator entitlement |
| `aws-public-s3` | Terraform AWS | LocalStack AWS | live demo available |
| `k8s-privileged-pod` | Kubernetes YAML/Helm/Kustomize | kind | offline demo available; live execution pending |
| `compose-exposed-admin` | Docker Compose | isolated Docker network | offline demo available; live probe pending |
| `onprem-ssh-password` | Ansible/cloud-init/libvirt/Proxmox-style IaC | VM/container-lab digital twin | offline demo available; microVM digital twin pending |
| `generic-plan-review` | unsupported IaC exports | none | plan-only available |
