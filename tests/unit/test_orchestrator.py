"""Orchestrator tests with the LLM client stubbed (no network)."""

from unittest.mock import AsyncMock

from codeguard.core.llm_client import ChatResponse, TokenUsage
from codeguard.pipeline import orchestrator as orch_mod
from codeguard.pipeline.orchestrator import CodeGuardOrchestrator


class _FakeClient:
    def __init__(self, chat):
        self.chat = chat

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return None


def _patch_client(monkeypatch, chat):
    monkeypatch.setattr(orch_mod, "LLMClient", lambda cfg: _FakeClient(chat))


async def test_successful_review_runs_summary(monkeypatch, config):
    chat = AsyncMock(
        return_value=ChatResponse(content="ok", usage=TokenUsage(total_tokens=10), model="m")
    )
    _patch_client(monkeypatch, chat)
    result = await CodeGuardOrchestrator(config).review("x = 1", "python")
    assert result.ok
    assert all(r.ok for r in result.agent_results.values())
    assert result.summary_result is not None and result.summary_result.summary == "ok"
    assert chat.await_count == 7
    assert result.total_tokens == 70


async def test_all_agents_failing_marks_review_failed(monkeypatch, config):
    chat = AsyncMock(side_effect=RuntimeError("401 Unauthorized"))
    _patch_client(monkeypatch, chat)
    result = await CodeGuardOrchestrator(config).review("x = 1", "python")
    assert not result.ok
    assert "401 Unauthorized" in result.error
    assert result.summary_result is None
    assert chat.await_count == 6  # summary agent is skipped
