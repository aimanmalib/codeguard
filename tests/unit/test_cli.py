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
