"""Evaluates test coverage and suggests missing test cases."""

from __future__ import annotations

from .base import BaseAgent, AgentResult


class TestingAgent(BaseAgent):
    name = "testing"
    description = "Evaluates test coverage and suggests missing test cases"

    SYSTEM = """You are the Testing Agent in a code review pipeline.
Evaluate: test coverage gaps, missing edge case tests, error path testing,
test quality (assertions, isolation), boundary value tests.
Output JSON with: function, file, severity, category, suggested_test (pytest snippet)."""

    async def execute(self, code: str, language: str = "", context: str = "") -> AgentResult:
        prompt = f"""Review the following {language or 'code'} for test coverage.

{f"Context: {context}" if context else ""}

CODE:
```
{code}
```

Return findings as JSON."""

        response = await self._call_mimo(prompt, self.SYSTEM)
        return AgentResult(
            agent_name=self.name, summary=response.content,
            tokens_used=response.usage.total_tokens, latency_ms=response.latency_ms,
            reasoning=response.reasoning_content,
        )
