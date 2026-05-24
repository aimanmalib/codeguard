"""Configuration for CodeGuard pipeline."""

from __future__ import annotations

import os
from typing import Optional

import yaml
from pydantic import BaseModel, Field


class MiMoConfig(BaseModel):
    """MiMo API settings."""
    api_key: str = Field(default_factory=lambda: os.environ.get("MIMO_API_KEY", ""))
    base_url: str = Field(
        default_factory=lambda: os.environ.get(
            "MIMO_BASE_URL", "https://token-plan-sgp.xiaomimimo.com/v1"
        )
    )
    model: str = "mimo-v2.5-pro"
    max_tokens: int = 4096
    temperature: float = 0.3  # Lower for code review accuracy
    timeout: int = 120
    max_retries: int = 3

    @property
    def headers(self) -> dict[str, str]:
        return {
            "api-key": self.api_key,  # MiMo Token Plan: api-key, NOT Bearer
            "Content-Type": "application/json",
        }


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
    mimo: MiMoConfig = Field(default_factory=MiMoConfig)
    review: ReviewConfig = Field(default_factory=ReviewConfig)
    output_format: str = "text"  # text | json | markdown | github-comment
    log_level: str = "INFO"

    @classmethod
    def from_yaml(cls, path: str) -> "CodeGuardConfig":
        with open(path) as f:
            return cls(**yaml.safe_load(f) or {})

    @classmethod
    def from_env(cls) -> "CodeGuardConfig":
        return cls()
