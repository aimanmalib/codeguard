"""CodeGuard Agents - 7 specialized AI agents for code review."""

from .base import BaseAgent, AgentResult
from .security import SecurityAgent
from .style import StyleAgent
from .complexity import ComplexityAgent
from .logic import LogicAgent
from .testing import TestingAgent
from .documentation import DocumentationAgent
from .summary import SummaryAgent

AGENT_REGISTRY: dict[str, type[BaseAgent]] = {
    "security": SecurityAgent,
    "style": StyleAgent,
    "complexity": ComplexityAgent,
    "logic": LogicAgent,
    "testing": TestingAgent,
    "documentation": DocumentationAgent,
    "summary": SummaryAgent,
}

def get_agent(name: str, **kwargs) -> BaseAgent:
    cls = AGENT_REGISTRY.get(name)
    if not cls:
        raise ValueError(f"Unknown agent: {name}. Available: {list(AGENT_REGISTRY)}")
    return cls(**kwargs)

__all__ = [
    "BaseAgent", "AgentResult", "AGENT_REGISTRY", "get_agent",
    "SecurityAgent", "StyleAgent", "ComplexityAgent", "LogicAgent",
    "TestingAgent", "DocumentationAgent", "SummaryAgent",
]
