# CodeGuard

> **Multi-agent code review for any OpenAI-compatible LLM**
>
> Six specialist agents review your code in parallel (security, style, complexity, logic, testing, documentation); a seventh merges their output into one prioritized report with an APPROVE / REQUEST_CHANGES / COMMENT recommendation.

[![CI](https://github.com/aimanmalib/codeguard/actions/workflows/ci.yml/badge.svg)](https://github.com/aimanmalib/codeguard/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Works with **OpenAI, OpenRouter, Ollama, llama.cpp, Groq, DeepSeek, Together, Mistral, Xiaomi MiMo**, or any endpoint that speaks the OpenAI `/chat/completions` protocol. Pick a provider with one config line, no code changes. The default is OpenAI.

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

## The 7 Agents

| # | Agent | Reviews | Output |
|---|-------|---------|--------|
| 1 | **Security** | Injection, secrets, crypto, validation | CWE-tagged findings |
| 2 | **Style** | Naming, formatting, idioms, dead code | Before/after suggestions |
| 3 | **Complexity** | Cyclomatic/cognitive complexity, duplication | Refactoring suggestions |
| 4 | **Logic** | Edge cases, null handling, race conditions | Bug scenarios + fixes |
| 5 | **Testing** | Coverage gaps, missing test cases | Pytest snippets |
| 6 | **Documentation** | Docstrings, type hints, TODO comments | Suggested docs |
| 7 | **Summary** | Aggregate, deduplicate, prioritize | APPROVE/CHANGES/COMMENT |

Each agent asks the model for JSON findings; CodeGuard passes the model's answer through as-is, so the exact shape depends on the model you use.

## Quick Start

```bash
git clone https://github.com/aimanmalib/codeguard.git
cd codeguard
python -m venv .venv && source .venv/bin/activate
pip install -e .

# OpenAI is the default provider: just set the key
export OPENAI_API_KEY="sk-..."

# Review a file (Markdown report in the terminal)
codeguard review --path ./src/main.py

# Review a directory, JSON report to a file
codeguard review --path ./src --format json --output report.json

# List the agents
codeguard agents
```

A review makes 7 LLM calls (6 in parallel, then the summary). If every review agent fails (wrong key, unreachable endpoint), the command exits with status 1 and prints the first error.

`--format` is `text` (rendered Markdown, the default), `markdown` (raw Markdown on stdout), or `json`. Status messages go to stderr, so `--format json` on stdout is pipe-friendly.

## Supported Providers

Built-in presets (from `src/codeguard/core/config.py`):

| Provider | `provider:` | Default model | Auth header | API key env var |
|----------|-------------|---------------|-------------|-----------------|
| OpenAI (default) | `openai` | `gpt-4o-mini` | Bearer | `OPENAI_API_KEY` |
| OpenRouter | `openrouter` | `openai/gpt-4o-mini` | Bearer | `OPENROUTER_API_KEY` |
| Ollama (local) | `ollama` | `llama3.1` | Bearer | `OLLAMA_API_KEY` (optional) |
| Groq | `groq` | `llama-3.3-70b-versatile` | Bearer | `GROQ_API_KEY` |
| DeepSeek | `deepseek` | `deepseek-chat` | Bearer | `DEEPSEEK_API_KEY` |
| Together | `together` | `meta-llama/Llama-3.3-70B-Instruct-Turbo` | Bearer | `TOGETHER_API_KEY` |
| Mistral | `mistral` | `mistral-small-latest` | Bearer | `MISTRAL_API_KEY` |
| Xiaomi MiMo | `mimo` | `mimo-v2.5-pro` | `api-key` | `MIMO_API_KEY` |

Every preset's base URL can be overridden with `<PROVIDER>_BASE_URL` (for example `OPENAI_BASE_URL`, `OLLAMA_BASE_URL`) or with `base_url` in the config file. That is also how you use any other OpenAI-compatible server (llama.cpp, vLLM, LM Studio, a local proxy).

## Configuration

Without `--config`, CodeGuard uses the `openai` preset and reads `OPENAI_API_KEY` / `OPENAI_BASE_URL` from the environment. To pick another provider or model, pass a YAML file:

```yaml
# codeguard.yaml
llm:
  provider: openrouter         # any preset name from the table above
  model: openai/gpt-4o         # optional; defaults to the preset's model
  # base_url: http://localhost:8080/v1  # optional; any OpenAI-compatible endpoint
  temperature: 0.3             # low for consistent severity classification
  max_tokens: 4096
  max_retries: 3               # retries on 429 / 5xx / network errors
```

```bash
export OPENROUTER_API_KEY="sk-or-..."
codeguard --config codeguard.yaml review --path ./src
```

The API key is read from the provider's env var. You can also set `api_key:` in the file, but keep such a file out of version control. Environment variables are not expanded inside the YAML.

## Development

```bash
pip install -e ".[dev]"
ruff check src/ tests/ && ruff format --check src/ tests/
pytest
```

The test suite mocks all HTTP calls, so it needs no API key. CI runs it on Python 3.10 to 3.13.

## Project Structure

```
src/codeguard/
├── cli.py                 # `codeguard` command (review, agents)
├── agents/                # 6 review agents + summary agent, registry in __init__.py
├── core/
│   ├── config.py          # provider presets, LLMConfig, YAML loading
│   ├── llm_client.py      # async OpenAI-compatible client (retries, usage tracking)
│   ├── mimo_client.py     # backward-compat import shim for llm_client
│   └── token_tracker.py   # per-agent token and latency metrics
└── pipeline/
    └── orchestrator.py    # parallel review phase, then summary
tests/unit/                # unit tests (HTTP mocked)
```

## Contributing and Security

See [CONTRIBUTING.md](CONTRIBUTING.md). Please report vulnerabilities privately, as described in [SECURITY.md](SECURITY.md).

## License

[MIT](LICENSE) © 2026 Muhammad Aiman

---

Built by [Sasa Teguh](https://sasateguh.com) · Malaysia
