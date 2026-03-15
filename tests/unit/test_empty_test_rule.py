from __future__ import annotations

from pathlib import Path

from testsniff.parser.loader import load_source
from testsniff.parser.module_context import ModuleContext
from testsniff.reporting.finding import Finding
from testsniff.rules.checks.empty_test import EmptyTestRule

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "empty_test"


def test_empty_test_rule_reports_pass_only_test() -> None:
    findings = _analyze_fixture("positive_pass.py")

    assert len(findings) == 1
    finding = findings[0]
    assert finding.rule_id == "TS001"
    assert finding.severity == "error"
    assert finding.confidence == "high"
    assert finding.line == 1


def test_empty_test_rule_reports_docstring_only_test() -> None:
    findings = _analyze_fixture("positive_docstring_only.py")

    assert len(findings) == 1
    assert findings[0].rule_id == "TS001"


def test_empty_test_rule_ignores_real_assertions() -> None:
    findings = _analyze_fixture("negative_assert.py")

    assert findings == []


def test_empty_test_rule_ignores_non_test_helpers() -> None:
    findings = _analyze_fixture("negative_helper_pass.py")

    assert findings == []


def _analyze_fixture(filename: str) -> list[Finding]:
    path = FIXTURES_DIR / filename
    module = ModuleContext.from_source(path, load_source(path))
    return EmptyTestRule().analyze(module)
