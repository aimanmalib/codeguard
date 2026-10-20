"""
CodeGuard — 7-Agent Code Review Automation.

Provider-agnostic: runs on any OpenAI-compatible /chat/completions endpoint
(OpenAI, OpenRouter, Ollama, llama.cpp, Groq, DeepSeek, ...).

Usage:
    codeguard review --path ./src/main.py
    codeguard review --path ./src --format json --output report.json
    codeguard agents
"""

__version__ = "1.0.0"
