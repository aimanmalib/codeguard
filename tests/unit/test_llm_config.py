"""Unit tests for multi-backend LLM configuration.

Covers the provider-agnostic LLMConfig: preset resolution, bearer vs api-key
auth styles, env-var fallbacks, and backward-compatible MiMoConfig behaviour.
"""

from codeguard.core.config import (
    DEFAULT_PROVIDER,
    PROVIDER_PRESETS,
    CodeGuardConfig,
    LLMConfig,
    MiMoConfig,
)


class TestProviderPresets:
    def test_known_providers_present(self):
        for provider in (
            "mimo",
            "openai",
            "openrouter",
            "ollama",
            "groq",
            "deepseek",
            "together",
            "mistral",
        ):
            assert provider in PROVIDER_PRESETS

    def test_default_provider_is_mimo(self):
        assert DEFAULT_PROVIDER == "mimo"


class TestLLMConfigPresetResolution:
    def test_openai_preset(self):
        c = LLMConfig(provider="openai", api_key="sk-test")
        assert c.base_url == "https://api.openai.com/v1"
        assert c.model == "gpt-4o-mini"
        assert c.auth_style == "bearer"

    def test_openrouter_preset(self):
        c = LLMConfig(provider="openrouter", api_key="or-test")
        assert "openrouter.ai" in c.base_url
        assert c.auth_style == "bearer"

    def test_ollama_preset(self):
        c = LLMConfig(provider="ollama")
        assert "localhost:11434" in c.base_url
        assert c.model == "llama3.1"

    def test_unknown_provider_falls_back_to_default(self):
        c = LLMConfig(provider="does-not-exist", api_key="x")
        assert "xiaomimimo.com" in c.base_url

    def test_groq_preset(self):
        c = LLMConfig(provider="groq", api_key="t")
        assert "api.groq.com" in c.base_url
        assert c.auth_style == "bearer"

    def test_deepseek_preset(self):
        c = LLMConfig(provider="deepseek", api_key="t")
        assert "api.deepseek.com" in c.base_url
        assert c.auth_style == "bearer"

    def test_together_preset(self):
        c = LLMConfig(provider="together", api_key="t")
        assert "api.together.xyz" in c.base_url
        assert c.auth_style == "bearer"

    def test_mistral_preset(self):
        c = LLMConfig(provider="mistral", api_key="t")
        assert "api.mistral.ai" in c.base_url
        assert c.auth_style == "bearer"

    def test_explicit_values_override_preset(self):
        c = LLMConfig(provider="openai", base_url="https://proxy.local/v1", model="custom")
        assert c.base_url == "https://proxy.local/v1"
        assert c.model == "custom"

    def test_default_temperature_low_for_code_review(self):
        """Code review uses a low temperature regardless of provider."""
        assert LLMConfig(provider="openai", api_key="x").temperature == 0.3


class TestAuthStyles:
    def test_bearer_auth_header(self):
        c = LLMConfig(provider="openai", api_key="sk-abc")
        assert c.headers["Authorization"] == "Bearer sk-abc"
        assert "api-key" not in c.headers

    def test_api_key_auth_header(self):
        c = LLMConfig(provider="mimo", api_key="mimo-secret")
        assert c.headers["api-key"] == "mimo-secret"
        assert "Authorization" not in c.headers

    def test_explicit_auth_style_override(self):
        c = LLMConfig(provider="mimo", api_key="k", auth_style="bearer")
        assert c.headers["Authorization"] == "Bearer k"


class TestEnvResolution:
    def test_openai_env_key(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-from-env")
        assert LLMConfig(provider="openai").api_key == "sk-from-env"

    def test_openrouter_env_base(self, monkeypatch):
        monkeypatch.setenv("OPENROUTER_API_KEY", "or-env")
        monkeypatch.setenv("OPENROUTER_BASE_URL", "https://env.openrouter/v1")
        c = LLMConfig(provider="openrouter")
        assert c.api_key == "or-env"
        assert c.base_url == "https://env.openrouter/v1"


class TestMiMoBackwardCompat:
    def test_mimo_config_defaults(self):
        c = MiMoConfig(api_key="test")
        assert c.provider == "mimo"
        assert c.model == "mimo-v2.5-pro"
        assert "xiaomimimo.com" in c.base_url
        assert c.headers["api-key"] == "test"
        assert c.temperature == 0.3

    def test_root_config_mimo_property_aliases_llm(self):
        c = CodeGuardConfig()
        assert c.mimo is c.llm

    def test_legacy_mimo_yaml_block_maps_to_llm(self):
        c = CodeGuardConfig(**{"mimo": {"api_key": "legacy", "model": "mimo-v2.5-pro"}})
        assert c.llm.api_key == "legacy"
        assert c.mimo.api_key == "legacy"

    def test_new_llm_yaml_block(self):
        c = CodeGuardConfig(**{"llm": {"provider": "openai", "api_key": "sk-x"}})
        assert c.llm.provider == "openai"
        assert c.llm.auth_style == "bearer"
