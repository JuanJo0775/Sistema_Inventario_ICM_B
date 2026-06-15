from __future__ import annotations

from pathlib import Path

import pytest

from scripts.security.run_security_scan import (
    TOOLS,
    _resolve_tools,
    _run_tool,
    _sanitize,
    build_parser,
)


class TestToolsConfig:
    def test_all_tools_defined(self):
        assert len(TOOLS) == 6

    def test_each_tool_has_required_keys(self):
        for tool in TOOLS:
            assert "name" in tool
            assert "cmd" in tool
            assert "desc" in tool
            assert isinstance(tool["cmd"], list)
            assert len(tool["cmd"]) > 0

    def test_tool_names_are_unique(self):
        names = [t["name"] for t in TOOLS]
        assert len(names) == len(set(names))

    def test_semgrep_has_ci_flags(self):
        semgrep = next(t for t in TOOLS if t["name"] == "semgrep")
        assert "ci_flags" in semgrep
        assert "--quiet" in semgrep["ci_flags"]

    def test_ruff_lint_cmd(self):
        ruff = next(t for t in TOOLS if t["name"] == "ruff lint")
        assert ruff["cmd"][0] == "ruff"
        assert ruff["cmd"][1] == "check"

    def test_bandit_cmd(self):
        bandit = next(t for t in TOOLS if t["name"] == "bandit")
        assert bandit["cmd"][0] == "bandit"
        assert "-r" in bandit["cmd"]

    def test_mypy_cmd(self):
        mypy = next(t for t in TOOLS if t["name"] == "mypy")
        assert mypy["cmd"][0] == "mypy"


class TestSanitize:
    def test_plain_text_passes_through(self):
        text = "Hello world 123"
        assert _sanitize(text) == text

    def test_ascii_punctuation_passes(self):
        text = "All checks passed!\n270 files already formatted"
        assert _sanitize(text) == text

    def test_unicode_box_chars_stripped(self):
        text = "\u250c\u2500\u2500\u2510\n\u2502 x \u2502\n\u2514\u2500\u2500\u2518"
        result = _sanitize(text)
        assert "\u250c" not in result
        assert "\u2502" not in result
        assert "\u2514" not in result

    def test_unicode_checkmark_stripped(self):
        text = "Result: \u2705 OK"
        result = _sanitize(text)
        assert "\u2705" not in result

    def test_unicode_xmark_stripped(self):
        text = "Result: \u274c FAIL"
        result = _sanitize(text)
        assert "\u274c" not in result

    def test_empty_string(self):
        assert _sanitize("") == ""


class TestRunTool:
    def test_dry_run_returns_ok_and_command(self):
        ok, output = _run_tool("test", ["echo", "hello"], "Test tool", dry_run=True)
        assert ok
        assert "echo hello" in output

    def test_dry_run_never_executes(self):
        ok, output = _run_tool(
            "test", ["nonexistent_cmd_xyz_123"], "Test", dry_run=True,
        )
        assert ok
        assert "nonexistent_cmd_xyz_123" in output

    def test_file_not_found_returns_fail(self):
        ok, output = _run_tool(
            "test", ["nonexistent_cmd_xyz_123"], "Test", dry_run=False,
        )
        assert not ok
        assert "NOT FOUND" in output

    def test_ci_flag_applies_ci_flags(self):
        ok, output = _run_tool(
            "test", ["echo", "hello"], "Test",
            dry_run=True, ci=True, ci_flags=["--quiet", "--error"],
        )
        assert " --quiet --error" in output

    def test_ci_flag_no_ci_flags_unchanged(self):
        ok, output = _run_tool(
            "test", ["echo", "hello"], "Test",
            dry_run=True, ci=True, ci_flags=None,
        )
        assert "--quiet" not in output
        assert "echo hello" in output


class TestResolveTools:
    def test_empty_only_returns_all(self):
        result = _resolve_tools("", "")
        assert len(result) == len(TOOLS)

    def test_only_selects_specific_tool(self):
        result = _resolve_tools("ruff lint", "")
        assert len(result) == 1
        assert result[0]["name"] == "ruff lint"

    def test_only_selects_multiple_tools(self):
        result = _resolve_tools("ruff lint,bandit", "")
        assert len(result) == 2
        names = {t["name"] for t in result}
        assert names == {"ruff lint", "bandit"}

    def test_skip_excludes_tool(self):
        result = _resolve_tools("", "mypy")
        names = {t["name"] for t in result}
        assert "mypy" not in names
        assert len(result) == len(TOOLS) - 1

    def test_skip_multiple_tools(self):
        result = _resolve_tools("", "pip-audit,mypy")
        assert len(result) == len(TOOLS) - 2

    def test_only_and_skip_both_empty_returns_all(self):
        result = _resolve_tools("", "")
        assert len(result) == len(TOOLS)

    def test_unknown_only_raises_system_exit(self):
        with pytest.raises(SystemExit, match="2"):
            _resolve_tools("unknown_tool_xyz", "")

    def test_unknown_skip_raises_system_exit(self):
        with pytest.raises(SystemExit, match="2"):
            _resolve_tools("", "unknown_tool_xyz")

    def test_only_returns_matching_tools(self):
        result = _resolve_tools("mypy,ruff lint", "")
        names = {t["name"] for t in result}
        assert names == {"mypy", "ruff lint"}
        assert len(result) == 2


class TestParser:
    def test_default_output_path(self):
        parser = build_parser()
        args = parser.parse_args([])
        assert "reporte_calidad_" in args.output
        assert args.output.endswith(".txt")

    def test_ci_flag(self):
        parser = build_parser()
        args = parser.parse_args(["--ci"])
        assert args.ci

    def test_only_flag(self):
        parser = build_parser()
        args = parser.parse_args(["--only", "ruff"])
        assert args.only == "ruff"

    def test_skip_flag(self):
        parser = build_parser()
        args = parser.parse_args(["--skip", "mypy"])
        assert args.skip == "mypy"

    def test_list_flag(self):
        parser = build_parser()
        args = parser.parse_args(["--list"])
        assert args.list

    def test_dry_run_flag(self):
        parser = build_parser()
        args = parser.parse_args(["--dry-run"])
        assert args.dry_run

    def test_output_custom(self):
        parser = build_parser()
        args = parser.parse_args(["--output", "/tmp/mi_reporte.txt"])
        assert args.output == "/tmp/mi_reporte.txt"

    def test_only_and_skip_parsed_together(self):
        parser = build_parser()
        args = parser.parse_args(["--only", "ruff", "--skip", "bandit"])
        assert args.only == "ruff"
        assert args.skip == "bandit"

    def test_default_only_is_empty(self):
        parser = build_parser()
        args = parser.parse_args([])
        assert args.only == ""

    def test_default_skip_is_empty(self):
        parser = build_parser()
        args = parser.parse_args([])
        assert args.skip == ""

    def test_default_ci_is_false(self):
        parser = build_parser()
        args = parser.parse_args([])
        assert not args.ci

    def test_default_list_is_false(self):
        parser = build_parser()
        args = parser.parse_args([])
        assert not args.list

    def test_default_dry_run_is_false(self):
        parser = build_parser()
        args = parser.parse_args([])
        assert not args.dry_run
