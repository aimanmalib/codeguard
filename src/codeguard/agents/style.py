"""Checks naming conventions, formatting, and language idioms."""

from __future__ import annotations

from .base import BaseAgent, AgentResult


class StyleAgent(BaseAgent):
    name = "style"
    description = "Checks naming conventions, formatting, and language idioms"

    SYSTEM = """You are the Style Agent in a code review pipeline.
Check for: naming conventions, function length (>50 lines), class complexity,
unused imports, magic numbers, dead code, language idioms, formatting consistency.
Output JSON findings with: file, line, severity, category, title, current, suggestion."""

    async def execute(self, code: str, language: str = "", context: str = "") -> AgentResult:
        prompt = f"""Review the following {language or 'code'} for style and conventions.

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
