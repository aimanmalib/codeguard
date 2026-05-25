"""Pipeline orchestrator for CodeGuard - runs all 7 agents in parallel/sequence."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Optional

from ..agents import AGENT_REGISTRY, get_agent
from ..agents.base import AgentResult
from ..core.config import CodeGuardConfig
from ..core.mimo_client import MiMoClient
from ..core.token_tracker import TokenTracker

logger = logging.getLogger(__name__)


@dataclass
class ReviewResult:
    status: str = "success"
    code: str = ""
    agent_results: dict[str, AgentResult] = field(default_factory=dict)
    summary_result: Optional[AgentResult] = None
    total_tokens: int = 0
    duration_s: float = 0.0

    @property
    def ok(self) -> bool:
        return self.status == "success"

    @property
    def total_findings(self) -> int:
        return sum(r.finding_count for r in self.agent_results.values())


class CodeGuardOrchestrator:
    """Coordinates 7 review agents.

    Flow:
    1. Run security, style, complexity, logic, testing, documentation in PARALLEL
    2. Collect all findings
    3. Feed to summary agent for final report
    """

    REVIEW_AGENTS = ["security", "style", "complexity", "logic", "testing", "documentation"]

    def __init__(self, config: CodeGuardConfig):
        self.config = config
        self.tracker = TokenTracker()

    async def review(self, code: str, language: str = "") -> ReviewResult:
        result = ReviewResult(code=code)
        self.tracker.start()

        async with MiMoClient(self.config.mimo) as client:
            try:
                # Phase 1: Run all review agents in parallel
                logger.info("[CodeGuard] Phase 1: Running 6 review agents in parallel")

                tasks = []
                for agent_name in self.REVIEW_AGENTS:
                    agent = get_agent(agent_name, config=self.config, client=client, tracker=self.tracker)
                    tasks.append(agent.run(code=code, language=language))

                results = await asyncio.gather(*tasks, return_exceptions=True)

                for agent_name, res in zip(self.REVIEW_AGENTS, results):
                    if isinstance(res, Exception):
                        result.agent_results[agent_name] = AgentResult(
                            agent_name=agent_name, status="failed", error=str(res)
                        )
                    else:
                        result.agent_results[agent_name] = res

                # Phase 2: Aggregate and summarize
                logger.info("[CodeGuard] Phase 2: Generating summary")

                findings_context = ""
                for name, r in result.agent_results.items():
                    if r.ok:
                        findings_context += f"\n=== {name.upper()} ===\n{r.summary}\n"

                summary_agent = get_agent("summary", config=self.config, client=client, tracker=self.tracker)
                result.summary_result = await summary_agent.run(code=code, context=findings_context)

            except Exception as e:
                logger.error(f"[CodeGuard] Fatal: {e}")
                result.status = "failed"

        self.tracker.end()
        result.total_tokens = self.tracker.total_tokens
        result.duration_s = self.tracker.duration_s
        return result
