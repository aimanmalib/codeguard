"""CodeGuard CLI."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from . import __version__
from .core.config import CodeGuardConfig
from .pipeline.orchestrator import CodeGuardOrchestrator

console = Console()

# Map file extensions to language names for the review prompt.
_EXT_TO_LANG = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".go": "go",
    ".rs": "rust",
    ".java": "java",
    ".rb": "ruby",
    ".php": "php",
    ".c": "c",
    ".h": "c",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".cs": "csharp",
    ".kt": "kotlin",
    ".swift": "swift",
    ".scala": "scala",
    ".sh": "bash",
    ".sql": "sql",
}


def _detect_language(suffix: str) -> str:
    """Best-effort language detection from a file extension."""
    return _EXT_TO_LANG.get(suffix.lower(), "auto")


@click.group()
@click.version_option(version=__version__, prog_name="codeguard")
@click.option("--config", "-c", type=click.Path(exists=True))
@click.option("--verbose", "-v", is_flag=True)
@click.pass_context
def main(ctx, config, verbose):
    """CodeGuard - 7-Agent Code Review Automation.

    Provider-agnostic: runs on any OpenAI-compatible LLM endpoint
    (OpenAI, OpenRouter, Ollama, MiMo, ...).
    """
    import logging

    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO)
    ctx.ensure_object(dict)
    ctx.obj["config"] = CodeGuardConfig.from_yaml(config) if config else CodeGuardConfig.from_env()


@main.command()
@click.option("--path", "-p", required=True, help="File or directory to review")
@click.option("--language", "-l", default="", help="Force language")
@click.option(
    "--format", "-f", "fmt", default="text", type=click.Choice(["text", "json", "markdown"])
)
@click.option("--output", "-o", default="", help="Output file")
@click.pass_context
def review(ctx, path, language, fmt, output):
    """Review code for quality, security, and style issues."""
    config = ctx.obj["config"]
    target = Path(path)

    if target.is_file():
        code = target.read_text()
        if not language:
            language = _detect_language(target.suffix)
    elif target.is_dir():
        # Concatenate source files
        parts = []
        for ext in [".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".rs"]:
            for f in target.rglob(f"*{ext}"):
                if "node_modules" not in str(f) and ".git" not in str(f):
                    parts.append(f"# File: {f.relative_to(target)}\n{f.read_text()}")
        code = "\n\n".join(parts)
    else:
        console.print(f"[red]Path not found: {path}[/]")
        sys.exit(1)

    console.print(
        Panel(
            f"[bold cyan]CodeGuard v{__version__}[/]\n"
            f"Target: {path} | Language: {language or 'auto'} | Format: {fmt}",
            title="Review Configuration",
        )
    )

    result = asyncio.run(_run_review(config, code, language))

    if result.ok:
        _display_results(result, fmt, output)
    else:
        console.print("[red]Review failed[/]")
        sys.exit(1)


@main.command()
def agents():
    """List all available agents."""
    from .agents import AGENT_REGISTRY

    table = Table(title="CodeGuard Agents", border_style="cyan")
    table.add_column("Name", style="bold")
    table.add_column("Description")
    for name, cls in AGENT_REGISTRY.items():
        table.add_row(name, cls.description)
    console.print(table)


async def _run_review(config, code, language):
    orchestrator = CodeGuardOrchestrator(config)
    return await orchestrator.review(code, language)


def _display_results(result, fmt, output):
    if fmt == "json":
        data = {
            "total_tokens": result.total_tokens,
            "duration_s": result.duration_s,
            "agents": {
                name: {"summary": r.summary, "tokens": r.tokens_used}
                for name, r in result.agent_results.items()
            },
        }
        text = json.dumps(data, indent=2)
        if output:
            Path(output).write_text(text)
        else:
            console.print(text)
    else:
        console.print()
        console.print(
            Panel(
                f"[bold green]Review Complete![/]\n\n"
                f"Tokens: {result.total_tokens:,}\n"
                f"Duration: {result.duration_s:.1f}s\n"
                f"Agents: {len(result.agent_results)}",
                title="Results",
                border_style="green",
            )
        )


if __name__ == "__main__":
    main()
