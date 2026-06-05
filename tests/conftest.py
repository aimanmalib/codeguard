"""Shared fixtures."""

import pytest
from codeguard.core.config import CodeGuardConfig, MiMoConfig


@pytest.fixture
def config():
    return CodeGuardConfig(mimo=MiMoConfig(api_key="test-key"))
