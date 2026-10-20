"""Unit tests for the OpenAI-compatible LLM client (HTTP mocked)."""

import json

import httpx
import pytest

from codeguard.core.config import LLMConfig
from codeguard.core.llm_client import ChatMessage, LLMClient


def _client(handler, **cfg) -> LLMClient:
    config = LLMConfig(provider="openai", api_key="k", retry_delay=0, **cfg)
    client = LLMClient(config)
    client._client = httpx.AsyncClient(
        base_url=config.base_url, headers=config.headers, transport=httpx.MockTransport(handler)
    )
    return client


def _ok(content="hi", usage=None):
    body = {"model": "m", "choices": [{"message": {"content": content}}]}
    if usage is not None:
        body["usage"] = usage
    return httpx.Response(200, json=body)


async def test_payload_disables_streaming_and_honours_zero_temperature():
    seen = {}

    def handler(request):
        seen.update(json.loads(request.content))
        return _ok()

    client = _client(handler)
    resp = await client.chat([ChatMessage("user", "x")], temperature=0.0)
    assert resp.content == "hi"
    assert seen["stream"] is False
    assert seen["temperature"] == 0.0


async def test_null_usage_and_content_are_tolerated():
    def handler(request):
        return httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": None}}],
                "usage": {"total_tokens": 7, "prompt_tokens_details": None},
            },
        )

    resp = await _client(handler).chat([ChatMessage("user", "x")])
    assert resp.content == ""
    assert resp.usage.total_tokens == 7
    assert resp.usage.cached_tokens == 0


async def test_retries_server_errors_then_succeeds():
    calls = []

    def handler(request):
        calls.append(1)
        return httpx.Response(503) if len(calls) < 2 else _ok("done")

    resp = await _client(handler, max_retries=3).chat([ChatMessage("user", "x")])
    assert resp.content == "done"
    assert len(calls) == 2


async def test_does_not_retry_auth_errors():
    calls = []

    def handler(request):
        calls.append(1)
        return httpx.Response(401, json={"error": "bad key"})

    with pytest.raises(httpx.HTTPStatusError):
        await _client(handler, max_retries=3).chat([ChatMessage("user", "x")])
    assert len(calls) == 1
