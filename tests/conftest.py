"""Shared fixtures."""

import pytest

from codeguard.core.config import CodeGuardConfig, LLMConfig


@pytest.fixture
def config():
    return CodeGuardConfig(llm=LLMConfig(provider="openai", api_key="test-key"))
