"""Configuration for CodeGuard pipeline.

CodeGuard speaks the OpenAI-compatible ``/chat/completions`` protocol, so it
works with any provider exposing that API: OpenAI, OpenRouter, Ollama, local
llama.cpp servers, Xiaomi MiMo Token Plan, and more. Pick a provider via
``LLMConfig(provider=...)`` or point ``base_url`` at any compatible endpoint.
"""

from __future__ import annotations

import os

import yaml
from pydantic import BaseModel, Field, model_validator

# Provider presets: base_url, auth header style, default model, and the env
# vars used to populate api_key / base_url when they aren't set explicitly.
# auth_style is "bearer" (Authorization: Bearer) or "api-key" (api-key header).
PROVIDER_PRESETS: dict[str, dict[str, str]] = {
    "mimo": {
        "base_url": "https://token-plan-sgp.xiaomimimo.com/v1",
        "auth_style": "api-key",
        "model": "mimo-v2.5-pro",
        "env_key": "MIMO_API_KEY",
        "env_base": "MIMO_BASE_URL",
    },
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "auth_style": "bearer",
        "model": "gpt-4o-mini",
        "env_key": "OPENAI_API_KEY",
        "env_base": "OPENAI_BASE_URL",
    },
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "auth_style": "bearer",
        "model": "openai/gpt-4o-mini",
        "env_key": "OPENROUTER_API_KEY",
        "env_base": "OPENROUTER_BASE_URL",
    },
    "ollama": {
        "base_url": "http://localhost:11434/v1",
        "auth_style": "bearer",
        "model": "llama3.1",
        "env_key": "OLLAMA_API_KEY",
        "env_base": "OLLAMA_BASE_URL",
    },
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "auth_style": "bearer",
        "model": "llama-3.3-70b-versatile",
        "env_key": "GROQ_API_KEY",
        "env_base": "GROQ_BASE_URL",
    },
    "deepseek": {
        "base_url": "https://api.deepseek.com/v1",
        "auth_style": "bearer",
        "model": "deepseek-chat",
        "env_key": "DEEPSEEK_API_KEY",
        "env_base": "DEEPSEEK_BASE_URL",
    },
    "together": {
        "base_url": "https://api.together.xyz/v1",
        "auth_style": "bearer",
        "model": "meta-llama/Llama-3.3-70B-Instruct-Turbo",
        "env_key": "TOGETHER_API_KEY",
        "env_base": "TOGETHER_BASE_URL",
    },
    "mistral": {
        "base_url": "https://api.mistral.ai/v1",
        "auth_style": "bearer",
        "model": "mistral-small-latest",
        "env_key": "MISTRAL_API_KEY",
        "env_base": "MISTRAL_BASE_URL",
    },
}

DEFAULT_PROVIDER = "mimo"


class LLMConfig(BaseModel):
    """Connection settings for any OpenAI-compatible chat completions endpoint.

    Empty ``api_key`` / ``base_url`` / ``model`` / ``auth_style`` fields are
    resolved from the selected provider preset (and its env vars) after init.
    A low default temperature (0.3) is used for code-review accuracy.
    """

    provider: str = DEFAULT_PROVIDER
    api_key: str = ""
    base_url: str = ""
    model: str = ""
    auth_style: str = ""  # "bearer" | "api-key" — resolved from provider if blank
    max_tokens: int = 4096
    temperature: float = 0.3  # Lower for code review accuracy
    top_p: float = 0.9
    timeout: int = 120
    max_retries: int = 3
    retry_delay: float = 1.0

    @model_validator(mode="after")
    def _resolve_provider_defaults(self) -> "LLMConfig":
        preset = PROVIDER_PRESETS.get(self.provider, PROVIDER_PRESETS[DEFAULT_PROVIDER])
        if not self.api_key:
            self.api_key = os.environ.get(preset["env_key"], "")
        if not self.base_url:
            self.base_url = os.environ.get(preset["env_base"], preset["base_url"])
        if not self.model:
            self.model = preset["model"]
        if not self.auth_style:
            self.auth_style = preset["auth_style"]
        return self

    @property
    def headers(self) -> dict[str, str]:
        """Auth + content headers, matching the provider's expected auth style."""
        headers = {"Content-Type": "application/json"}
        if self.auth_style == "bearer":
            headers["Authorization"] = f"Bearer {self.api_key}"
        else:
            headers["api-key"] = self.api_key
        return headers


class MiMoConfig(LLMConfig):
    """Backward-compatible alias defaulting to the Xiaomi MiMo Token Plan API.

    Retained so existing configs/tests keep working. New code should prefer
    :class:`LLMConfig` with an explicit ``provider``.
    """

    provider: str = "mimo"


class ReviewConfig(BaseModel):
    """Review pipeline settings."""

    severity_threshold: str = "warning"  # info | warning | error | critical
    max_suggestions: int = 20
    include_security: bool = True
    include_style: bool = True
    include_complexity: bool = True
    include_tests: bool = True
    include_docs: bool = True
    language: str = "auto"  # auto-detect from file extensions
    ignore_patterns: list[str] = Field(default_factory=lambda: ["*.min.js", "*.lock"])


class CodeGuardConfig(BaseModel):
    """Root configuration."""

    llm: LLMConfig = Field(default_factory=LLMConfig)
    review: ReviewConfig = Field(default_factory=ReviewConfig)
    output_format: str = "text"  # text | json | markdown | github-comment
    log_level: str = "INFO"

    @model_validator(mode="before")
    @classmethod
    def _accept_legacy_mimo_key(cls, data):
        """Map a legacy top-level ``mimo:`` block onto ``llm`` for old configs."""
        if isinstance(data, dict) and "mimo" in data and "llm" not in data:
            data = dict(data)
            data["llm"] = data.pop("mimo")
        return data

    @property
    def mimo(self) -> LLMConfig:
        """Deprecated alias for :attr:`llm` (kept for backward compatibility)."""
        return self.llm

    @classmethod
    def from_yaml(cls, path: str) -> "CodeGuardConfig":
        with open(path) as f:
            return cls(**yaml.safe_load(f) or {})

    @classmethod
    def from_env(cls) -> "CodeGuardConfig":
        return cls()
