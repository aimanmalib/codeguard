"""OpenAI-compatible chat completions client for CodeGuard.

Works with any provider that speaks the OpenAI ``/chat/completions`` protocol
(OpenAI, OpenRouter, Ollama, llama.cpp, Xiaomi MiMo Token Plan, ...). The auth
header style (bearer vs api-key) comes from :class:`LLMConfig`.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field

import httpx

from .config import LLMConfig

logger = logging.getLogger(__name__)


@dataclass
class TokenUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cached_tokens: int = 0

    def add(self, other: TokenUsage) -> None:
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
    reasoning_content: str | None = None
    usage: TokenUsage = field(default_factory=TokenUsage)
    model: str = ""
    latency_ms: float = 0.0


class LLMClient:
    """Async client for any OpenAI-compatible chat completions endpoint.

    Auth style (``Authorization: Bearer`` vs ``api-key`` header) and the base
    URL are taken from the supplied :class:`LLMConfig`, so the same client
    serves OpenAI, OpenRouter, Ollama, MiMo Token Plan, etc.
    """

    def __init__(self, config: LLMConfig):
        self.config = config
        self._client: httpx.AsyncClient | None = None
        self.total_usage = TokenUsage()

    async def __aenter__(self) -> LLMClient:
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
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> ChatResponse:
        payload = {
            "model": self.config.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "max_tokens": max_tokens if max_tokens is not None else self.config.max_tokens,
            "temperature": temperature if temperature is not None else self.config.temperature,
            # Explicit: some OpenAI-compatible servers stream when this is omitted,
            # and this client parses a single JSON body.
            "stream": False,
        }

        start = time.monotonic()
        for attempt in range(self.config.max_retries):
            try:
                resp = await self._client.post("/chat/completions", json=payload)
                resp.raise_for_status()
                data = resp.json()
                break
            except (httpx.HTTPStatusError, httpx.TransportError) as exc:
                retryable = not isinstance(exc, httpx.HTTPStatusError) or _is_retryable_status(
                    exc.response.status_code
                )
                if retryable and attempt < self.config.max_retries - 1:
                    await asyncio.sleep(self.config.retry_delay * (2**attempt))
                else:
                    raise

        latency = (time.monotonic() - start) * 1000
        choice = data["choices"][0]
        message = choice.get("message") or {}
        usage_data = data.get("usage") or {}
        usage = TokenUsage(
            prompt_tokens=usage_data.get("prompt_tokens") or 0,
            completion_tokens=usage_data.get("completion_tokens") or 0,
            total_tokens=usage_data.get("total_tokens") or 0,
            cached_tokens=(usage_data.get("prompt_tokens_details") or {}).get("cached_tokens") or 0,
        )
        self.total_usage.add(usage)

        return ChatResponse(
            content=message.get("content") or "",
            reasoning_content=message.get("reasoning_content"),
            usage=usage,
            model=data.get("model", ""),
            latency_ms=latency,
        )


def _is_retryable_status(status: int) -> bool:
    """Retry rate limits and server errors; fail fast on other client errors."""
    return status == 429 or status >= 500


# Backward-compatible alias. New code should use LLMClient.
MiMoClient = LLMClient
