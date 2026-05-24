"""Identifies security vulnerabilities, injection risks, and unsafe patterns."""

from __future__ import annotations

from .base import BaseAgent, AgentResult


class SecurityAgent(BaseAgent):
    name = "security"
    description = "Identifies security vulnerabilities, injection risks, and unsafe patterns"

    SYSTEM = """You are the Security Agent in a code review pipeline.
Analyze code for: SQL injection, XSS, CSRF, hardcoded secrets, insecure crypto,
path traversal, unsafe deserialization, missing input validation, insecure dependencies.
For each finding output JSON with: file, line, severity (critical|error|warning|info),
category, title, description, suggestion, cwe."""

    async def execute(self, code: str, language: str = "", context: str = "") -> AgentResult:
        prompt = f"""Review the following {language or 'code'} for security vulnerabilities.

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
