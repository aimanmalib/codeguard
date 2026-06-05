"""Base agent for CodeGuard."""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional

from ..core.config import CodeGuardConfig
from ..core.mimo_client import ChatMessage, ChatResponse, MiMoClient
from ..core.token_tracker import TokenTracker

logger = logging.getLogger(__name__)


@dataclass
class AgentResult:
    agent_name: str
    status: str = "success"
    findings: list[dict[str, Any]] = field(default_factory=list)
    summary: str = ""
    tokens_used: int = 0
    latency_ms: float = 0.0
    error: Optional[str] = None
    reasoning: Optional[str] = None

    @property
    def ok(self) -> bool:
        return self.status == "success"

    @property
    def finding_count(self) -> int:
        return len(self.findings)

    @property
    def critical_count(self) -> int:
        return sum(1 for f in self.findings if f.get("severity") == "critical")

    @property
    def error_count(self) -> int:
        return sum(1 for f in self.findings if f.get("severity") == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for f in self.findings if f.get("severity") == "warning")


class BaseAgent(ABC):
    name: str = "base"
    description: str = "Base agent"

    def __init__(self, config: CodeGuardConfig, client: MiMoClient, tracker: TokenTracker):
        self.config = config
        self.client = client
        self.tracker = tracker

    async def _call_mimo(self, prompt: str, system: str = "") -> ChatResponse:
        messages = []
        if system:
            messages.append(ChatMessage(role="system", content=system))
        messages.append(ChatMessage(role="user", content=prompt))

        start = time.monotonic()
        try:
            response = await self.client.chat(messages)
            latency = (time.monotonic() - start) * 1000
            self.tracker.record(self.name, response.usage.total_tokens, latency)
            return response
        except Exception:
            latency = (time.monotonic() - start) * 1000
            self.tracker.record(self.name, 0, latency, errors=1)
            raise

    @abstractmethod
    async def execute(self, code: str, language: str = "", context: str = "") -> AgentResult: ...

    async def run(self, code: str, language: str = "", context: str = "") -> AgentResult:
        try:
            return await self.execute(code=code, language=language, context=context)
        except Exception as e:
            return AgentResult(agent_name=self.name, status="failed", error=str(e))
