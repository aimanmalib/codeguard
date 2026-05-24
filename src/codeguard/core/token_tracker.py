"""Token consumption tracking for CodeGuard."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class AgentMetrics:
    agent_name: str
    call_count: int = 0
    total_tokens: int = 0
    total_latency_ms: float = 0.0
    errors: int = 0

    @property
    def avg_latency_ms(self) -> float:
        return self.total_latency_ms / max(self.call_count, 1)

    @property
    def tokens_per_call(self) -> float:
        return self.total_tokens / max(self.call_count, 1)


class TokenTracker:
    def __init__(self, output_dir: str = "./output"):
        self._agents: dict[str, AgentMetrics] = {}
        self._start: Optional[float] = None
        self._end: Optional[float] = None
        self._output_dir = Path(output_dir)
        self._run_id = time.strftime("%Y%m%d_%H%M%S")

    def start(self) -> None:
        self._start = time.monotonic()

    def end(self) -> None:
        self._end = time.monotonic()

    def record(self, agent: str, tokens: int, latency_ms: float, errors: int = 0) -> None:
        if agent not in self._agents:
            self._agents[agent] = AgentMetrics(agent_name=agent)
        m = self._agents[agent]
        m.call_count += 1
        m.total_tokens += tokens
        m.total_latency_ms += latency_ms
        m.errors += errors

    @property
    def total_tokens(self) -> int:
        return sum(m.total_tokens for m in self._agents.values())

    @property
    def duration_s(self) -> float:
        if not self._start:
            return 0
        return (self._end or time.monotonic()) - self._start

    def report(self) -> str:
        lines = [
            "=" * 50,
            "  CodeGuard Token Report",
            f"  Run: {self._run_id}",
            "=" * 50,
            f"  Duration: {self.duration_s:.1f}s | Total: {self.total_tokens:,} tokens",
            "",
        ]
        for name, m in sorted(self._agents.items(), key=lambda x: -x[1].total_tokens):
            lines.append(f"  {name:<18} {m.call_count:>4} calls  {m.total_tokens:>8,} tok  {m.avg_latency_ms:>6.0f}ms")
        lines.append("=" * 50)
        return "\n".join(lines)

    def save(self, path: Optional[str] = None) -> Path:
        out = Path(path) if path else self._output_dir / "metrics" / f"{self._run_id}.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "run_id": self._run_id,
            "duration_s": round(self.duration_s, 2),
            "total_tokens": self.total_tokens,
            "agents": {
                name: {"calls": m.call_count, "tokens": m.total_tokens, "avg_latency_ms": round(m.avg_latency_ms, 1)}
                for name, m in self._agents.items()
            },
        }
        out.write_text(json.dumps(data, indent=2))
        return out
