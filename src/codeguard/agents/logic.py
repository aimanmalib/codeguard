"""Detects logical errors, edge cases, and potential bugs."""

from __future__ import annotations

from .base import BaseAgent, AgentResult


class LogicAgent(BaseAgent):
    name = "logic"
    description = "Detects logical errors, edge cases, and potential bugs"

    SYSTEM = """You are the Logic Agent in a code review pipeline.
Look for: off-by-one errors, null/None handling, unhandled exceptions,
integer overflow, floating point comparison, boundary checks, boolean logic,
state management bugs, race conditions, resource leaks.
Output JSON with: file, line, severity, category, edge_case, fix."""

    async def execute(self, code: str, language: str = "", context: str = "") -> AgentResult:
        prompt = f"""Review the following {language or "code"} for logical errors and edge cases.

{f"Context: {context}" if context else ""}

CODE:
```
{code}
```

Return findings as JSON."""

        response = await self._call_mimo(prompt, self.SYSTEM)
        return AgentResult(
            agent_name=self.name,
            summary=response.content,
            tokens_used=response.usage.total_tokens,
            latency_ms=response.latency_ms,
            reasoning=response.reasoning_content,
        )
