from __future__ import annotations

import json

from testsniff.config.types import ScanConfig
from testsniff.reporting.finding import ExampleSnippet, Finding
from testsniff.reporting.render import render_result
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


def _sample_result() -> ScanResult:
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
    finding = Finding(
        rule_id="TS001",
        headline="Example finding",
        severity="warning",
        confidence="high",
        path="tests/test_example.py",
        line=12,
        column=1,
        why="Explanation",
        fix="Do the thing",
        example=ExampleSnippet(
            bad="def test_bad():\n    pass",
            good="def test_good():\n    assert True",
        ),
        references=("https://example.invalid/rules/TS001",),
    )
    return ScanResult(
        config=config,
        findings=[finding],
        parse_failures=[],
        files_scanned=1,
        files_skipped=0,
        elapsed_ms=1.0,
        exit_code=1,
    )

