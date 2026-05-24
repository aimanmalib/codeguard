"""MiMo V2.5 Pro API client for CodeGuard."""

from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from typing import AsyncIterator, Optional

import httpx

from .config import MiMoConfig

logger = logging.getLogger(__name__)


@dataclass
class TokenUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cached_tokens: int = 0

    def add(self, other: "TokenUsage") -> None:
        self.prompt_tokens += other.prompt_tokens
        self.completion_tokens += other.completion_tokens
        self.total_tokens += other.total_tokens
        self.cached_tokens += other.cached_tokens


@dataclass
class ChatMessage:
    role: str
    content: str


@dataclass
class ChatResponse:
    content: str
    reasoning_content: Optional[str] = None
    usage: TokenUsage = field(default_factory=TokenUsage)
    model: str = ""
    latency_ms: float = 0.0


class MiMoClient:
    """Async MiMo API client. Uses api-key header (NOT Authorization: Bearer)."""

    def __init__(self, config: MiMoConfig):
        self.config = config
        self._client: Optional[httpx.AsyncClient] = None
        self.total_usage = TokenUsage()

    async def __aenter__(self) -> "MiMoClient":
        self._client = httpx.AsyncClient(
            base_url=self.config.base_url,
            headers=self.config.headers,
            timeout=httpx.Timeout(self.config.timeout),
        )
        return self

    async def __aexit__(self, *args) -> None:
        if self._client:
            await self._client.aclose()

    async def chat(
        self,
        messages: list[ChatMessage],
        *,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> ChatResponse:
        payload = {
            "model": self.config.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "max_tokens": max_tokens or self.config.max_tokens,
            "temperature": temperature or self.config.temperature,
        }

        start = time.monotonic()
        for attempt in range(self.config.max_retries):
            try:
                resp = await self._client.post("/chat/completions", json=payload)
                resp.raise_for_status()
                data = resp.json()
                break
            except (httpx.HTTPStatusError, httpx.ConnectError) as e:
                if attempt < self.config.max_retries - 1:
                    await asyncio.sleep(1.0 * (2 ** attempt))
                else:
                    raise

        latency = (time.monotonic() - start) * 1000
        choice = data["choices"][0]
        usage_data = data.get("usage", {})
        usage = TokenUsage(
            prompt_tokens=usage_data.get("prompt_tokens", 0),
            completion_tokens=usage_data.get("completion_tokens", 0),
            total_tokens=usage_data.get("total_tokens", 0),
            cached_tokens=usage_data.get("prompt_tokens_details", {}).get("cached_tokens", 0),
        )
        self.total_usage.add(usage)

        return ChatResponse(
            content=choice.get("message", {}).get("content", ""),
            reasoning_content=choice.get("message", {}).get("reasoning_content"),
            usage=usage,
            model=data.get("model", ""),
            latency_ms=latency,
        )
