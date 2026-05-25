"""Unit tests for token tracking."""

import pytest
from codeguard.core.token_tracker import TokenTracker, AgentMetrics


class TestTokenTracker:
    def test_initial_state(self):
        t = TokenTracker()
        assert t.total_tokens == 0

    def test_record(self):
        t = TokenTracker()
        t.record("security", tokens=500, latency_ms=100)
        assert t.total_tokens == 500

    def test_multiple_agents(self):
        t = TokenTracker()
        t.record("security", 500, 100)
        t.record("style", 300, 80)
        assert t.total_tokens == 800

    def test_duration(self):
        import time
        t = TokenTracker()
        t.start()
        time.sleep(0.01)
        t.end()
        assert t.duration_s > 0

    def test_report(self):
        t = TokenTracker()
        t.record("security", 500, 100)
        report = t.report()
        assert "CodeGuard" in report
        assert "security" in report


class TestAgentMetrics:
    def test_defaults(self):
        m = AgentMetrics(agent_name="test")
        assert m.call_count == 0
        assert m.avg_latency_ms == 0
        assert m.tokens_per_call == 0

    def test_calculations(self):
        m = AgentMetrics(agent_name="test", call_count=2, total_tokens=1000, total_latency_ms=200)
        assert m.avg_latency_ms == 100
        assert m.tokens_per_call == 500
