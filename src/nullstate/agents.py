from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any

import requests

from .llm_providers import chat_completions_url, normalize_provider, resolve_base_url
from .metrics import ModelCallMetrics, metrics_from_openai_response, offline_agent_metrics


@dataclass(frozen=True)
class AgentResult:
    role: str
    model: str
    content: str
    metrics: ModelCallMetrics


class LlmAgent:
    def __init__(
        self,
        role: str,
        model: str,
        base_url: str | None = None,
        api_key: str | None = None,
        provider: str | None = None,
    ) -> None:
        self.role = role
        self.model = model
        self.provider = normalize_provider(provider or os.getenv("NULLSTATE_LLM_PROVIDER"))
        self.base_url = resolve_base_url(
            provider=self.provider,
            explicit_base_url=base_url,
            shared_base_url=os.getenv("NULLSTATE_LLM_BASE_URL"),
        )
        self.api_key = api_key or os.getenv("NULLSTATE_LLM_API_KEY", "")

    def complete(self, system_prompt: str, user_prompt: str, offline: bool) -> AgentResult:
        if offline or not self.base_url:
            return AgentResult(
                role=self.role,
                model="offline-mock",
                content=self._offline_response(user_prompt),
                metrics=offline_agent_metrics(self.role),
            )

        endpoint = chat_completions_url(self.base_url, provider=self.provider)
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        started = time.monotonic()
        response = requests.post(
            endpoint,
            headers=headers,
            data=json.dumps(
                {
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": 0.2,
                }
            ),
            timeout=120,
        )
        latency = time.monotonic() - started
        response.raise_for_status()
        payload: dict[str, Any] = response.json()
        content = payload["choices"][0]["message"]["content"]
        return AgentResult(
            role=self.role,
            model=self.model,
            content=content,
            metrics=metrics_from_openai_response(
                role=self.role,
                model=self.model,
                latency_seconds=latency,
                response_payload=payload,
            ),
        )

    def _offline_response(self, user_prompt: str) -> str:
        if "AWS_S3_PUBLIC_ACCESS_BLOCK_DISABLED" in user_prompt:
            if self.role == "red":
                return "Offline red team selected an anonymous S3 read hypothesis for the public access block exposure."
            return "Offline blue team recommended enabling all S3 public access block controls."
        if "AZURE_STORAGE_PUBLIC_BLOB" in user_prompt:
            if self.role == "red":
                return "Offline red team selected the anonymous Azure Blob read exploit for the detected public container."
            return (
                "Offline blue team confirmed the exposure and recommended setting container_access_type to private "
                "and allow_nested_items_to_be_public to false."
            )
        if self.role == "red":
            return "Offline red team selected an exploit hypothesis for the detected exposure."
        return "Offline blue team confirmed the exposure and recommended the deterministic remediation."
