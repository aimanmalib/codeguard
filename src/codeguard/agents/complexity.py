"""Measures cyclomatic complexity and suggests refactoring."""

from __future__ import annotations

from .base import BaseAgent, AgentResult


class ComplexityAgent(BaseAgent):
    name = "complexity"
    description = "Measures cyclomatic complexity and suggests refactoring"

    SYSTEM = """You are the Complexity Agent in a code review pipeline.
Analyze: cyclomatic complexity per function (warn >10, error >20), cognitive complexity,
code duplication, long parameter lists (>4 params), god classes (>500 lines),
circular dependencies, deeply nested conditionals, refactoring opportunities.
Output JSON with: file, function, line, cyclomatic_complexity, severity, refactoring."""

    async def execute(self, code: str, language: str = "", context: str = "") -> AgentResult:
        prompt = f"""Review the following {language or "code"} for complexity.

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
