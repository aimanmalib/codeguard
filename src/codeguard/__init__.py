"""
CodeGuard — 7-Agent Code Review Automation.

Provider-agnostic: runs on any OpenAI-compatible /chat/completions endpoint
(OpenAI, OpenRouter, Ollama, llama.cpp, Xiaomi MiMo, ...).

Usage:
    codeguard review --diff changes.patch
    codeguard scan --path ./src
    codeguard pr --repo owner/repo --number 42
"""

__version__ = "1.0.0"
