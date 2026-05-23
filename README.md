# MiMo CodeGuard

> **7-Agent Code Review Automation powered by Xiaomi MiMo V2.5 Pro**
>
> Parallel security, style, complexity, logic, testing, and documentation analysis with AI-powered summary and actionable recommendations.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![Tests: 42](https://img.shields.io/badge/tests-42-brightgreen.svg)](tests/)
[![LOC: 2,800+](https://img.shields.io/badge/LOC-2%2C800%2B-orange.svg)](src/)
[![MiMo V2.5 Pro](https://img.shields.io/badge/MiMo-V2.5%20Pro-orange.svg)](https://platform.xiaomimimo.com)

---

## Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                    MiMo CodeGuard Pipeline                     │
│               Powered by Xiaomi MiMo V2.5 Pro                 │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  Phase 1: PARALLEL REVIEW (6 agents)                          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                      │
│  │ Security  │ │  Style   │ │Complexity│                      │
│  │  Agent   │ │  Agent   │ │  Agent   │                      │
│  └──────────┘ └──────────┘ └──────────┘                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                      │
│  │  Logic   │ │ Testing  │ │   Docs   │                      │
│  │  Agent   │ │  Agent   │ │  Agent   │                      │
│  └──────────┘ └──────────┘ └──────────┘                      │
│         │          │           │                               │
│         └──────────┼───────────┘                               │
│                    ▼                                            │
│  Phase 2: AGGREGATE                                            │
│  ┌─────────────────────────────────┐                          │
│  │        Summary Agent            │                          │
│  │  Deduplicate · Prioritize ·    │                          │
│  │  Score · Decision               │                          │
│  └─────────────────────────────────┘                          │
│                    │                                            │
│                    ▼                                            │
│  ┌─────────────────────────────────┐                          │
│  │     Token Tracker & Report      │                          │
│  └─────────────────────────────────┘                          │
│                                                                │
│  API: token-plan-sgp.xiaomimimo.com/v1/chat/completions       │
│  Auth: api-key header · Model: mimo-v2.5-pro                  │
│  Phase 1 runs 6 agents concurrently (asyncio.gather)          │
└────────────────────────────────────────────────────────────────┘
```

## 7 Specialized Agents

| # | Agent | Reviews | Output |
|---|-------|---------|--------|
| 1 | **Security** | Injection, secrets, crypto, validation | CWE-tagged findings |
| 2 | **Style** | Naming, formatting, idioms, dead code | Before/after suggestions |
| 3 | **Complexity** | Cyclomatic/cognitive complexity, duplication | Refactoring suggestions |
| 4 | **Logic** | Edge cases, null handling, race conditions | Bug scenarios + fixes |
| 5 | **Testing** | Coverage gaps, missing test cases | Pytest snippets |
| 6 | **Documentation** | Docstrings, type hints, TODO comments | Suggested docs |
| 7 | **Summary** | Aggregate, deduplicate, prioritize | APPROVE/CHANGES/COMMENT |

## Why MiMo V2.5 Pro?

1. **Low temperature reasoning** — Code review at temp=0.3 benefits from MiMo's deterministic `reasoning_content` for consistent severity classification
2. **Parallel agent efficiency** — 6 concurrent API calls via asyncio with MiMo's 100 RPM / 10M TPM rate limits
3. **Structured JSON output** — MiMo produces valid JSON for findings without schema enforcement
4. **Cost efficiency** — Token Plan pricing makes per-PR review viable (~$0.01/review at ~5K tokens)

## Quick Start

```bash
pip install -e ".[dev]"
export MIMO_API_KEY="your-key"

# Review a file
codeguard review --path ./src/main.py

# Review a directory
codeguard review --path ./src --format json --output report.json

# List agents
codeguard agents
```

## Token Consumption

Per review (single file ~200 LOC):
- 6 parallel agents: ~500 tokens each = ~3,000 tokens
- Summary agent: ~800 tokens
- **Total: ~3,800 tokens per review**

Daily estimate (50 PRs): ~190K tokens/day

## Project Structure

```
mimo-codeguard/
├── src/codeguard/
│   ├── __init__.py
│   ├── cli.py
│   ├── agents/
│   │   ├── __init__.py           # Registry
│   │   ├── base.py               # BaseAgent + AgentResult
│   │   ├── security.py           # Agent 1
│   │   ├── style.py              # Agent 2
│   │   ├── complexity.py         # Agent 3
│   │   ├── logic.py              # Agent 4
│   │   ├── testing.py            # Agent 5
│   │   ├── documentation.py      # Agent 6
│   │   └── summary.py            # Agent 7
│   ├── core/
│   │   ├── config.py
│   │   ├── mimo_client.py
│   │   └── token_tracker.py
│   └── pipeline/
│       └── orchestrator.py
├── tests/
│   ├── unit/
│   │   ├── test_config.py
│   │   ├── test_agents.py
│   │   └── test_token_tracker.py
│   └── conftest.py
├── pyproject.toml
├── LICENSE
└── README.md
```

## License

MIT License

---

**Built with Xiaomi MiMo V2.5 Pro** via Token Plan API
`token-plan-sgp.xiaomimimo.com/v1`
