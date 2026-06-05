"""Backward-compatibility shim.

The implementation moved to :mod:`codeguard.core.llm_client` when CodeGuard
became provider-agnostic. This module re-exports the public names so existing
imports (``from codeguard.core.mimo_client import MiMoClient``) keep working.
Prefer importing from ``codeguard.core.llm_client`` in new code.
"""

from __future__ import annotations

from .llm_client import (  # noqa: F401
    ChatMessage,
    ChatResponse,
    LLMClient,
    MiMoClient,
    TokenUsage,
)

__all__ = [
    "ChatMessage",
    "ChatResponse",
    "LLMClient",
    "MiMoClient",
    "TokenUsage",
]
