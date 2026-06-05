"""Checks docstrings, comments, and documentation completeness."""

from __future__ import annotations

from .base import BaseAgent, AgentResult


class DocumentationAgent(BaseAgent):
    name = "documentation"
    description = "Checks docstrings, comments, and documentation completeness"

    SYSTEM = """You are the Documentation Agent in a code review pipeline.
Check for: missing docstrings, docstring format, parameter docs, missing type hints,
outdated comments, TODO/FIXME/HACK comments, README needs.
Output JSON with: file, line, severity, category, suggested_doc."""

    async def execute(self, code: str, language: str = "", context: str = "") -> AgentResult:
        prompt = f"""Review the following {language or "code"} for documentation quality.

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
