from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any


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
