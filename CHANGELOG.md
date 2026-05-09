# Changelog

All notable changes to this project will be documented here.

## Unreleased

- Added Terraform Azure public blob demo flow.
- Added sandbox backend registry and `nullstate sandbox` commands.
- Added model metrics artifact support.
- Added DevSecOps repository documentation and GitHub workflow templates.
- Documented AMD Developer Cloud / DigitalOcean primary compute path with Fireworks fallback.
- Added vLLM metrics scraping and GPU snapshot evidence collection.
- Added scaffolded AWS, Kubernetes, Docker Compose, on-prem, and plan-only scenarios.
- Added Docker Compose file for LocalStack Azure token-based startup.
- Added offline deterministic run support for AWS, Kubernetes, Docker Compose, on-prem, and generic plan-review scenarios.
- Added branded Nullstate CLI banner for demo recordings.
- Added automatic scenario and target inference for `nullstate run`.
- Added sandbox runtime probes to `nullstate sandbox status`.
- Decoupled static/offline IaC mode from model usage; configured model endpoints are now used unless `--mock-agents` is passed.
- Added role-specific red/blue model endpoint configuration and per-role vLLM metrics snapshots.
- Added live Terraform apply/re-apply support for Terraform-backed LocalStack scenarios.
- Added MI300X model-serving scripts for Qwen3.5 on SGLang and Gemma 4 on vLLM ROCm.
- Added guided CLI workflow hints, `nullstate status`, automatic sandbox env-file discovery, and latest/nested report lookup.
