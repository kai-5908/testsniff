from __future__ import annotations

import runpy
import sys

import typer.main

import testsniff.cli.main as cli_main
from testsniff.compat.ruff_style import format_compact_header
from testsniff.reporting.finding import ExampleSnippet, Finding


def test_main_invokes_typer_app(monkeypatch) -> None:
    calls: list[str] = []

    monkeypatch.setattr(cli_main, "app", lambda: calls.append("called"))

    cli_main.main()

    assert calls == ["called"]


def test_module_entrypoint_invokes_main(monkeypatch) -> None:
    calls: list[str] = []

    def fake_call(self, *args, **kwargs) -> None:
        calls.append("called")

    monkeypatch.setattr(typer.main.Typer, "__call__", fake_call)
    monkeypatch.delitem(sys.modules, "testsniff.cli.main", raising=False)

    runpy.run_module("testsniff.cli.main", run_name="__main__")

    assert calls == ["called"]


def test_format_compact_header_matches_ruff_style_contract() -> None:
    finding = Finding(
        rule_id="TS001",
        headline="Test body is empty",
        severity="error",
        confidence="high",
        path="tests/test_example.py",
        line=3,
        column=5,
        why="Explanation",
        fix="Fix it",
        example=ExampleSnippet(bad="pass", good="assert True"),
        references=(),
    )

    assert (
        format_compact_header(finding)
        == "tests/test_example.py:3:5: error[high] TS001 Test body is empty"
    )
