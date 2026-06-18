import unittest

from nullstate.llm_providers import (
    CLAUDE_OPENAI_BASE_URL,
    GOOGLE_OPENAI_BASE_URL,
    chat_completions_url,
    normalize_provider,
    resolve_base_url,
)


class LlmProviderTests(unittest.TestCase):
    def test_chat_completions_url_handles_self_hosted_v1_and_google_paths(self):
        self.assertEqual(
            chat_completions_url("http://127.0.0.1:8000"),
            "http://127.0.0.1:8000/v1/chat/completions",
        )
        self.assertEqual(
            chat_completions_url("http://127.0.0.1:8000/v1"),
            "http://127.0.0.1:8000/v1/chat/completions",
        )
        self.assertEqual(
            chat_completions_url("https://api.fireworks.ai/inference/v1"),
            "https://api.fireworks.ai/inference/v1/chat/completions",
        )
        self.assertEqual(
            chat_completions_url("https://generativelanguage.googleapis.com/v1beta/openai", provider="google"),
            "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        )
        self.assertEqual(
            chat_completions_url("https://api.anthropic.com/v1", provider="claude"),
            "https://api.anthropic.com/v1/chat/completions",
        )

    def test_google_provider_supplies_default_base_url_without_requiring_user_to_know_it(self):
        self.assertEqual(
            resolve_base_url(
                provider="google",
                explicit_base_url=None,
                role_base_url=None,
                shared_base_url="http://localhost:8000",
            ),
            GOOGLE_OPENAI_BASE_URL,
        )

    def test_claude_provider_supplies_default_base_url_without_requiring_user_to_know_it(self):
        self.assertEqual(
            resolve_base_url(
                provider="claude",
                explicit_base_url=None,
                role_base_url=None,
                shared_base_url="http://localhost:8000",
            ),
            CLAUDE_OPENAI_BASE_URL,
        )

    def test_explicit_base_url_overrides_provider_default(self):
        self.assertEqual(
            resolve_base_url(
                provider="google",
                explicit_base_url="http://proxy.local/openai",
                role_base_url=None,
                shared_base_url=None,
            ),
            "http://proxy.local/openai",
        )

    def test_normalizes_aliases_and_rejects_unsupported_providers(self):
        self.assertEqual(normalize_provider("gemini"), "google")
        self.assertEqual(normalize_provider("anthropic"), "claude")
        self.assertEqual(normalize_provider("vllm"), "custom")
        with self.assertRaisesRegex(ValueError, "Unsupported LLM provider"):
            normalize_provider("mistral")


if __name__ == "__main__":
    unittest.main()
