from __future__ import annotations

import json

from testsniff.config.types import Confidence, ScanConfig, Severity
from testsniff.reporting.finding import ExampleSnippet, Finding, ParseFailure
from testsniff.reporting.render import render_result, resolve_exit_code, sort_findings
from testsniff.services.scan import ScanResult


def test_render_human_includes_confidence_and_sections() -> None:
    result = _sample_result()

    rendered = render_result(result, "human")

    assert "warning[TS001][confidence=high]" in rendered
    assert "WHY: Explanation" in rendered
    assert "FIX: Do the thing" in rendered
    assert "# Bad:" in rendered
    assert "# Good:" in rendered


def test_render_json_emits_canonical_structure() -> None:
    result = _sample_result()

    payload = json.loads(render_result(result, "json"))

    assert payload["tool"] == "testsniff"
    assert payload["findings"][0]["rule_id"] == "TS001"
    assert payload["findings"][0]["location"]["line"] == 12


def test_render_compact_uses_lint_style_single_line_output() -> None:
    rendered = render_result(_sample_result(), "compact")

    assert rendered == "tests/test_example.py:12:1: warning[high] TS001 Example finding\n"


def test_render_compact_returns_no_findings_when_scan_is_clean() -> None:
    rendered = render_result(_sample_result(findings=[]), "compact")

    assert rendered == "No findings.\n"


def test_render_human_includes_parse_failures() -> None:
    rendered = render_result(
        _sample_result(
            parse_failures=[ParseFailure(path="tests/bad.py", message="invalid syntax")]
        ),
        "human",
    )

    assert "parse_error: tests/bad.py: invalid syntax" in rendered


def test_render_human_returns_no_findings_when_scan_is_clean() -> None:
    rendered = render_result(_sample_result(findings=[]), "human")

    assert rendered == "No findings.\n"


def test_resolve_exit_code_prioritizes_failures_over_findings() -> None:
    finding = _sample_result().findings[0]
    parse_failure = ParseFailure(path="tests/bad.py", message="invalid syntax")

    assert resolve_exit_code([], []) == 0
    assert resolve_exit_code([finding], []) == 1
    assert resolve_exit_code([finding], [parse_failure]) == 2


def test_sort_findings_orders_by_location_then_severity_and_confidence() -> None:
    findings = [
        _sample_finding(rule_id="TS002", severity="warning", confidence="medium"),
        _sample_finding(rule_id="TS001", severity="error", confidence="high"),
        _sample_finding(path="tests/a.py", line=1, column=1, rule_id="TS003"),
    ]

    ordered = sort_findings(findings)

    assert [finding.rule_id for finding in ordered] == ["TS003", "TS001", "TS002"]


def _sample_result(
    *,
    findings: list[Finding] | None = None,
    parse_failures: list[ParseFailure] | None = None,
) -> ScanResult:
    config = ScanConfig(
        target_paths=("tests",),
        include_patterns=("test_*.py",),
        exclude_patterns=(),
        selected_rule_ids=(),
        ignored_rule_ids=(),
        minimum_confidence="medium",
        minimum_severity="info",
        output_format="human",
    )
    return ScanResult(
        config=config,
        findings=findings if findings is not None else [_sample_finding()],
        parse_failures=parse_failures or [],
        files_scanned=1,
        files_skipped=0,
        elapsed_ms=1.0,
        exit_code=1,
    )


def _sample_finding(
    *,
    path: str = "tests/test_example.py",
    line: int = 12,
    column: int = 1,
    rule_id: str = "TS001",
    severity: Severity = "warning",
    confidence: Confidence = "high",
) -> Finding:
    return Finding(
        rule_id=rule_id,
        headline="Example finding",
        severity=severity,
        confidence=confidence,
        path=path,
        line=line,
        column=column,
        why="Explanation",
        fix="Do the thing",
        example=ExampleSnippet(
            bad="def test_bad():\n    pass",
            good="def test_good():\n    assert True",
        ),
        references=("https://example.invalid/rules/TS001",),
    )
