from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse


GOOGLE_OPENAI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai"
CLAUDE_OPENAI_BASE_URL = "https://api.anthropic.com/v1"
SUPPORTED_PROVIDERS = {"claude", "custom", "google", "openai-compatible"}


@dataclass(frozen=True)
class LlmEndpointConfig:
    provider: str
    base_url: str | None
    api_key: str


def normalize_provider(provider: str | None) -> str:
    if not provider:
        return "openai-compatible"
    normalized = provider.strip().lower().replace("_", "-")
    aliases = {
        "openai": "openai-compatible",
        "openai-compatible": "openai-compatible",
        "custom": "custom",
        "self-hosted": "custom",
        "vllm": "custom",
        "sglang": "custom",
        "anthropic": "claude",
        "claude": "claude",
        "gemini": "google",
        "google": "google",
        "google-ai-studio": "google",
    }
    resolved = aliases.get(normalized)
    if resolved is None or resolved not in SUPPORTED_PROVIDERS:
        known = ", ".join(sorted(SUPPORTED_PROVIDERS))
        raise ValueError(f"Unsupported LLM provider {provider!r}. Supported providers: {known}")
    return resolved


def resolve_base_url(
    *,
    provider: str,
    explicit_base_url: str | None,
    role_base_url: str | None = None,
    shared_base_url: str | None = None,
) -> str | None:
    if explicit_base_url:
        return explicit_base_url
    if role_base_url:
        return role_base_url
    if provider == "google":
        return GOOGLE_OPENAI_BASE_URL
    if provider == "claude":
        return CLAUDE_OPENAI_BASE_URL
    if shared_base_url:
        return shared_base_url
    return None


def chat_completions_url(base_url: str, *, provider: str = "openai-compatible") -> str:
    normalized_provider = normalize_provider(provider)
    trimmed = base_url.rstrip("/")
    parsed = urlparse(trimmed)
    path = parsed.path.rstrip("/")
    if path.endswith("/chat/completions"):
        return trimmed
    if normalized_provider == "google":
        return trimmed + "/chat/completions"
    if path.endswith("/v1") or path.endswith("/openai"):
        return trimmed + "/chat/completions"
    return trimmed + "/v1/chat/completions"
