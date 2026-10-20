"""Tests for CLI helpers."""

from codeguard.cli import _detect_language


class TestDetectLanguage:
    def test_python(self):
        assert _detect_language(".py") == "python"

    def test_typescript(self):
        assert _detect_language(".ts") == "typescript"
        assert _detect_language(".tsx") == "typescript"

    def test_case_insensitive(self):
        assert _detect_language(".PY") == "python"

    def test_unknown_extension_returns_auto(self):
        assert _detect_language(".xyz") == "auto"

    def test_go_and_rust(self):
        assert _detect_language(".go") == "go"
        assert _detect_language(".rs") == "rust"


class TestReviewCommand:
    """CLI review output, with the pipeline stubbed out (no network)."""

    @staticmethod
    def _result(ok=True):
        from codeguard.agents.base import AgentResult
        from codeguard.pipeline.orchestrator import ReviewResult

        agents = {
            "security": AgentResult(agent_name="security", summary="SQL injection on line 4"),
            "style": AgentResult(agent_name="style", status="failed", error="boom"),
        }
        if not ok:
            return ReviewResult(status="failed", error="all review agents failed (x)")
        return ReviewResult(
            agent_results=agents,
            summary_result=AgentResult(agent_name="summary", summary="REQUEST_CHANGES"),
            total_tokens=123,
        )

    def _invoke(self, monkeypatch, tmp_path, result, *args):
        from click.testing import CliRunner

        from codeguard import cli

        async def fake_run(config, code, language):
            return result

        monkeypatch.setattr(cli, "_run_review", fake_run)
        src = tmp_path / "a.py"
        src.write_text("x = 1\n")
        return CliRunner().invoke(cli.main, ["review", "-p", str(src), *args])

    def test_json_report_includes_findings_status_and_summary(self, monkeypatch, tmp_path):
        import json

        out = tmp_path / "r.json"
        res = self._invoke(monkeypatch, tmp_path, self._result(), "-f", "json", "-o", str(out))
        assert res.exit_code == 0, res.output
        data = json.loads(out.read_text())
        assert data["agents"]["security"]["summary"] == "SQL injection on line 4"
        assert data["agents"]["style"] == {
            "status": "failed",
            "summary": "",
            "tokens": 0,
            "error": "boom",
        }
        assert data["summary"]["report"] == "REQUEST_CHANGES"

    def test_markdown_report_shows_agent_output(self, monkeypatch, tmp_path):
        res = self._invoke(monkeypatch, tmp_path, self._result(), "-f", "markdown")
        assert res.exit_code == 0
        assert "SQL injection on line 4" in res.output
        assert "REQUEST_CHANGES" in res.output
        assert "Agent failed: boom" in res.output

    def test_failed_review_exits_nonzero_with_reason(self, monkeypatch, tmp_path):
        res = self._invoke(monkeypatch, tmp_path, self._result(ok=False))
        assert res.exit_code == 1
        assert "all review agents failed" in res.output
