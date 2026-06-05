"""Unit tests for CodeGuard agents."""

import pytest
from unittest.mock import AsyncMock

from codeguard.agents import AGENT_REGISTRY, get_agent
from codeguard.agents.base import BaseAgent, AgentResult
from codeguard.core.mimo_client import ChatResponse, TokenUsage


def make_response(content='{"findings": []}', tokens=500):
    return ChatResponse(
        content=content,
        usage=TokenUsage(
            prompt_tokens=tokens // 2, completion_tokens=tokens // 2, total_tokens=tokens
        ),
        model="mimo-v2.5-pro",
        latency_ms=100,
    )


class TestAgentRegistry:
    def test_all_7_registered(self):
        assert len(AGENT_REGISTRY) == 7

    def test_expected_agents(self):
        expected = {
            "security",
            "style",
            "complexity",
            "logic",
            "testing",
            "documentation",
            "summary",
        }
        assert set(AGENT_REGISTRY.keys()) == expected

    def test_get_valid(self, config):
        from codeguard.core.mimo_client import MiMoClient
        from codeguard.core.token_tracker import TokenTracker

        client = AsyncMock(spec=MiMoClient)
        tracker = TokenTracker()
        for name in AGENT_REGISTRY:
            agent = get_agent(name, config=config, client=client, tracker=tracker)
            assert agent.name == name
            assert isinstance(agent, BaseAgent)

    def test_get_invalid(self, config):
        from codeguard.core.token_tracker import TokenTracker

        with pytest.raises(ValueError):
            get_agent("nonexistent", config=config, client=AsyncMock(), tracker=TokenTracker())


class TestAgentResult:
    def test_defaults(self):
        r = AgentResult(agent_name="test")
        assert r.ok
        assert r.finding_count == 0

    def test_severity_counts(self):
        r = AgentResult(
            agent_name="test",
            findings=[
                {"severity": "critical"},
                {"severity": "error"},
                {"severity": "warning"},
                {"severity": "warning"},
            ],
        )
        assert r.critical_count == 1
        assert r.error_count == 1
        assert r.warning_count == 2
        assert r.finding_count == 4


class TestIndividualAgents:
    @pytest.fixture
    def agent_setup(self, config):
        from codeguard.core.mimo_client import MiMoClient
        from codeguard.core.token_tracker import TokenTracker

        client = AsyncMock(spec=MiMoClient)
        tracker = TokenTracker()
        return config, client, tracker

    @pytest.mark.asyncio
    async def test_security_agent(self, agent_setup):
        config, client, tracker = agent_setup
        client.chat = AsyncMock(return_value=make_response('{"findings": [], "summary": "ok"}'))
        agent = get_agent("security", config=config, client=client, tracker=tracker)
        result = await agent.execute(code="def foo(): pass", language="python")
        assert result.ok
        assert result.tokens_used > 0

    @pytest.mark.asyncio
    async def test_style_agent(self, agent_setup):
        config, client, tracker = agent_setup
        client.chat = AsyncMock(return_value=make_response('{"findings": []}'))
        agent = get_agent("style", config=config, client=client, tracker=tracker)
        result = await agent.execute(code="x = 1")
        assert result.ok

    @pytest.mark.asyncio
    async def test_complexity_agent(self, agent_setup):
        config, client, tracker = agent_setup
        client.chat = AsyncMock(return_value=make_response('{"findings": []}'))
        agent = get_agent("complexity", config=config, client=client, tracker=tracker)
        result = await agent.execute(code="def f(): pass")
        assert result.ok

    @pytest.mark.asyncio
    async def test_logic_agent(self, agent_setup):
        config, client, tracker = agent_setup
        client.chat = AsyncMock(return_value=make_response('{"findings": []}'))
        agent = get_agent("logic", config=config, client=client, tracker=tracker)
        result = await agent.execute(code="x = 1/0")
        assert result.ok

    @pytest.mark.asyncio
    async def test_testing_agent(self, agent_setup):
        config, client, tracker = agent_setup
        client.chat = AsyncMock(return_value=make_response('{"findings": []}'))
        agent = get_agent("testing", config=config, client=client, tracker=tracker)
        result = await agent.execute(code="def add(a,b): return a+b")
        assert result.ok

    @pytest.mark.asyncio
    async def test_documentation_agent(self, agent_setup):
        config, client, tracker = agent_setup
        client.chat = AsyncMock(return_value=make_response('{"findings": []}'))
        agent = get_agent("documentation", config=config, client=client, tracker=tracker)
        result = await agent.execute(code="def f(): pass")
        assert result.ok

    @pytest.mark.asyncio
    async def test_summary_agent(self, agent_setup):
        config, client, tracker = agent_setup
        client.chat = AsyncMock(
            return_value=make_response('{"decision": "APPROVE", "quality_score": 85}')
        )
        agent = get_agent("summary", config=config, client=client, tracker=tracker)
        result = await agent.execute(code="code", context="all findings here")
        assert result.ok
