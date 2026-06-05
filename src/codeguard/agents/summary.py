"""Aggregates findings into a prioritized review report."""

from __future__ import annotations

from .base import BaseAgent, AgentResult


class SummaryAgent(BaseAgent):
    name = "summary"
    description = "Aggregates findings into a prioritized review report"

    SYSTEM = """You are the Summary Agent in a code review pipeline.
Aggregate findings from 6 agents: deduplicate, prioritize by severity,
group related issues, generate actionable summary, score quality 0-100,
highlight top 3 critical issues, suggest decision: APPROVE/REQUEST_CHANGES/COMMENT.
Output JSON with: decision, quality_score, by_severity, top_issues, strengths, improvements."""

    async def execute(self, code: str, language: str = "", context: str = "") -> AgentResult:
        prompt = f"""Review the following {language or "code"} for summarize findings.

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
