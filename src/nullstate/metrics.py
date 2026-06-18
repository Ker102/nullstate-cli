from __future__ import annotations

import re
import shutil
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests


@dataclass(frozen=True)
class ModelCallMetrics:
    role: str
    model: str
    latency_seconds: float
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    output_tokens_per_second: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def metrics_from_openai_response(
    *, role: str, model: str, latency_seconds: float, response_payload: dict[str, Any]
) -> ModelCallMetrics:
    usage = response_payload.get("usage") or {}
    prompt_tokens = int(usage.get("prompt_tokens") or 0)
    completion_tokens = int(usage.get("completion_tokens") or 0)
    total_tokens = int(usage.get("total_tokens") or prompt_tokens + completion_tokens)
    output_tps = completion_tokens / latency_seconds if latency_seconds > 0 else 0.0
    return ModelCallMetrics(
        role=role,
        model=model,
        latency_seconds=latency_seconds,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        output_tokens_per_second=round(output_tps, 3),
    )


def offline_agent_metrics(role: str, model: str = "offline-mock") -> ModelCallMetrics:
    return ModelCallMetrics(
        role=role,
        model=model,
        latency_seconds=0.0,
        prompt_tokens=0,
        completion_tokens=0,
        total_tokens=0,
        output_tokens_per_second=0.0,
    )


def parse_vllm_metrics(metrics_text: str) -> dict[str, float]:
    wanted = {
        "vllm:generation_tokens_total": "generation_tokens_total",
        "vllm:request_success_total": "request_success_total",
        "vllm:num_requests_running": "num_requests_running",
        "vllm:gpu_cache_usage_perc": "gpu_cache_usage_perc",
    }
    parsed: dict[str, float] = {}
    for line in metrics_text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        match = re.match(r"^([A-Za-z0-9_:]+)(?:\{[^}]*\})?\s+([-+]?[0-9]*\.?[0-9]+)", line)
        if not match:
            continue
        metric_name, raw_value = match.groups()
        if metric_name in wanted:
            parsed[wanted[metric_name]] = parsed.get(wanted[metric_name], 0.0) + float(raw_value)
    return parsed


def classify_endpoint(*, base_url: str | None, offline: bool) -> str:
    if offline or not base_url:
        return "offline"
    host = urlparse(base_url).hostname or ""
    managed_domains = (
        "fireworks.ai",
        "together.ai",
        "openai.com",
        "anthropic.com",
        "generativelanguage.googleapis.com",
    )
    if any(host == domain or host.endswith(f".{domain}") for domain in managed_domains):
        return "managed"
    if host in {"localhost", "127.0.0.1", "::1"}:
        return "self-hosted"
    return "amd-gpu-hosted"


def collect_run_metrics(*, run_dir: Path, base_url: str | None, offline: bool, stage: str) -> dict[str, Any]:
    endpoint_type = classify_endpoint(base_url=base_url, offline=offline)
    summary: dict[str, Any] = {
        "endpoint_type": endpoint_type,
        "base_url_host": _safe_host(base_url),
        "vllm_metrics": {},
        "vllm_metrics_artifact": None,
        "gpu_snapshot": gpu_snapshot(),
    }
    if offline or not base_url:
        return summary

    metrics_url = base_url.rstrip("/") + "/metrics"
    try:
        response = requests.get(metrics_url, timeout=10)
        response.raise_for_status()
    except requests.RequestException as error:
        summary["vllm_metrics_error"] = str(error)
        return summary

    artifact = run_dir / f"vllm-metrics-{stage}.prom"
    artifact.write_text(response.text, encoding="utf-8")
    summary["vllm_metrics"] = parse_vllm_metrics(response.text)
    summary["vllm_metrics_artifact"] = artifact.name
    return summary


def gpu_snapshot(command_runner=None) -> dict[str, Any]:
    runner = command_runner or _run_gpu_command
    attempted = ["amd-smi", "rocm-smi"]
    for command in attempted:
        result = runner(command)
        if result is None:
            continue
        return {
            "status": "available",
            "command": command,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
        }
    return {"status": "unavailable", "attempted": attempted}


def _run_gpu_command(command: str) -> subprocess.CompletedProcess[str] | None:
    executable = shutil.which(command)
    if not executable:
        return None
    args = [executable, "static"] if command == "amd-smi" else [executable]
    return subprocess.run(args, text=True, capture_output=True, check=False, timeout=15)


def _safe_host(base_url: str | None) -> str | None:
    if not base_url:
        return None
    return urlparse(base_url).hostname
