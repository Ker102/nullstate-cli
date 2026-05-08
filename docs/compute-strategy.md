# AMD Compute Strategy

## Decision

Use the harder AMD Developer Cloud / DigitalOcean route as the primary path for the case study. Keep Fireworks AI as a contingency endpoint if GPU access is delayed.

## Why primary path is DigitalOcean/AMD Developer Cloud

- It produces stronger evidence for the hackathon: model serving, ROCm, vLLM/SGLang, GPU observability, and operational setup.
- It gives a better personal learning outcome because the work includes real DevOps, cloud access, security boundaries, and inference operations.
- It supports the project thesis: private or self-controlled model inference for sensitive IaC and security evidence.
- It creates better case-study material than calling a hosted API only.

## Why Fireworks stays as fallback

- It can unblock the demo if AMD Developer Cloud access is delayed.
- It keeps the red/blue agent loop working through an OpenAI-compatible endpoint.
- It is still relevant to the AMD ecosystem, but it should be positioned as managed inference rather than private local/owned serving.

## Execution plan

### Track A - DigitalOcean baseline without GPU

Set up the non-GPU platform first:

- project/repo secrets
- hardened control droplet or container host
- Docker and compose baseline
- LocalStack Azure sandbox
- nullstate CLI installation
- GitHub Actions environment configuration
- run artifact storage layout
- basic monitoring and logs

This work is useful even before the GPU is available.

### Track B - AMD GPU inference

When MI300X access is available:

- provision AMD Developer Cloud / DigitalOcean GPU instance
- install ROCm stack or use provider image
- serve model with vLLM or SGLang using an OpenAI-compatible API
- expose only the required API path to the nullstate operator environment
- record model name, context length, ROCm version, GPU model, memory, throughput, and latency
- save vLLM `/metrics` snapshots and `amd-smi` or `rocm-smi` output into the case-study evidence folder

### Track C - Fireworks contingency

If GPU access blocks the submission:

- configure `NULLSTATE_LLM_BASE_URL` for Fireworks-compatible endpoint
- run the same nullstate demo
- document this as the managed-inference fallback
- keep the DigitalOcean/AMD setup as the next milestone rather than hiding the blocker

## Demo positioning

Preferred story:

```text
nullstate runs local IaC security validation and can use a private AMD MI300X-hosted model endpoint for red/blue reasoning over security evidence.
```

Fallback story:

```text
nullstate is model-provider portable through OpenAI-compatible endpoints. The same CLI can run against managed inference while the private AMD GPU endpoint is being provisioned.
```

## Evidence checklist

- `runs/<id>/report.md`
- `runs/<id>/metrics.json`
- vLLM `/metrics` before/after snapshots
- `amd-smi` or `rocm-smi` output
- ROCm version
- model server launch command
- sanitized network diagram
- screenshots of GPU utilization and CLI run
- note whether the run used DigitalOcean/AMD GPU, local mock mode, or Fireworks fallback

## Risks

| Risk | Impact | Mitigation |
|---|---|---|
| AMD Developer Cloud access delayed | High | Build DO baseline and use Fireworks fallback |
| GPU image/ROCm mismatch | Medium | Prefer provider image; document exact versions |
| Model too large or slow | Medium | Start with one model for both red and blue roles |
| Endpoint exposed publicly | High | restrict ingress, use token auth, document network boundary |
| Case study overclaims private inference | High | label each run by actual endpoint type |
