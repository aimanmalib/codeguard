# CodeGuard

> **7-Agent Code Review Automation for any OpenAI-compatible LLM**
>
> Parallel security, style, complexity, logic, testing, and documentation analysis with AI-powered summary and actionable recommendations.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![CI](https://github.com/aimanmalib/codeguard/actions/workflows/ci.yml/badge.svg)](https://github.com/aimanmalib/codeguard/actions/workflows/ci.yml)
[![Tests: 44](https://img.shields.io/badge/tests-44-brightgreen.svg)](tests/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Works with **OpenAI, OpenRouter, Ollama, llama.cpp, Xiaomi MiMo**, or any endpoint that speaks the OpenAI `/chat/completions` protocol. Pick a provider with one config line — no code changes.

---

## Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                    CodeGuard Pipeline                         │
│              Any OpenAI-compatible LLM backend                │
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
│  Protocol: OpenAI-compatible /chat/completions                │
│  Auth: bearer token or api-key header (per provider)          │
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

## Supported Providers

CodeGuard talks to any OpenAI-compatible `/chat/completions` endpoint. Built-in presets:

| Provider | `provider=` | Default model | Auth | Env vars |
|----------|-------------|---------------|------|----------|
| OpenAI | `openai` | `gpt-4o-mini` | Bearer | `OPENAI_API_KEY`, `OPENAI_BASE_URL` |
| OpenRouter | `openrouter` | `openai/gpt-4o-mini` | Bearer | `OPENROUTER_API_KEY` |
| Ollama (local) | `ollama` | `llama3.1` | Bearer | `OLLAMA_BASE_URL` |
| Groq | `groq` | `llama-3.3-70b-versatile` | Bearer | `GROQ_API_KEY` |
| DeepSeek | `deepseek` | `deepseek-chat` | Bearer | `DEEPSEEK_API_KEY` |
| Together | `together` | `meta-llama/Llama-3.3-70B-Instruct-Turbo` | Bearer | `TOGETHER_API_KEY` |
| Mistral | `mistral` | `mistral-small-latest` | Bearer | `MISTRAL_API_KEY` |
| Xiaomi MiMo | `mimo` | `mimo-v2.5-pro` | api-key | `MIMO_API_KEY` |

Point `base_url` at any other compatible endpoint (llama.cpp, vLLM, LM Studio, a local proxy) and it just works. Code review runs at a low default temperature (0.3) for consistent severity classification regardless of provider.

## Quick Start

```bash
pip install -e ".[dev]"

# Pick any provider — set its API key (OpenAI shown here)
export OPENAI_API_KEY="sk-your-key-here"

# Review a file
codeguard review --path ./src/main.py

# Review a directory
codeguard review --path ./src --format json --output report.json

# List agents
codeguard agents
```

## Configuration

```yaml
# codeguard.yaml
llm:
  provider: openai          # openai | openrouter | ollama | mimo
  api_key: ${OPENAI_API_KEY}
  # base_url and model default from the provider preset; override if needed
  temperature: 0.3          # low for code-review accuracy
  max_retries: 3

review:
  severity_threshold: warning
  include_security: true
  include_style: true
```

## Token Consumption

Per review (single file ~200 LOC):
- 6 parallel agents: ~500 tokens each = ~3,000 tokens
- Summary agent: ~800 tokens
- **Total: ~3,800 tokens per review**

Daily estimate (50 PRs): ~190K tokens/day

## Project Structure

```
codeguard/
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
│   │   ├── config.py             # multi-provider presets
│   │   ├── llm_client.py         # OpenAI-compatible client
│   │   ├── mimo_client.py        # backward-compat shim → llm_client
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

**Provider-agnostic** — works with OpenAI, OpenRouter, Ollama, llama.cpp, Xiaomi MiMo, or any OpenAI-compatible `/chat/completions` endpoint.
