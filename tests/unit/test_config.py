"""Unit tests for CodeGuard configuration."""

import pytest
from codeguard.core.config import CodeGuardConfig, MiMoConfig, ReviewConfig


class TestMiMoConfig:
    def test_default_model(self):
        c = MiMoConfig(api_key="test")
        assert c.model == "mimo-v2.5-pro"

    def test_api_key_header_not_bearer(self):
        """MiMo Token Plan uses api-key header, NOT Authorization: Bearer."""
        c = MiMoConfig(api_key="my-key")
        assert "api-key" in c.headers
        assert "Authorization" not in c.headers

    def test_default_temperature_low(self):
        """Code review should use lower temperature for accuracy."""
        c = MiMoConfig(api_key="test")
        assert c.temperature == 0.3

    def test_base_url(self):
        c = MiMoConfig(api_key="test")
        assert "token-plan-sgp.xiaomimimo.com" in c.base_url


class TestReviewConfig:
    def test_defaults(self):
        c = ReviewConfig()
        assert c.severity_threshold == "warning"
        assert c.include_security is True
        assert c.max_suggestions == 20


class TestCodeGuardConfig:
    def test_from_env(self, monkeypatch):
        monkeypatch.setenv("MIMO_API_KEY", "env-key")
        c = CodeGuardConfig.from_env()
        assert c.mimo.api_key == "env-key"

    def test_output_format_default(self):
        c = CodeGuardConfig()
        assert c.output_format == "text"
