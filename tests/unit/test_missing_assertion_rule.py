from __future__ import annotations

from pathlib import Path

from testsniff.parser.loader import load_source
from testsniff.parser.module_context import ModuleContext
from testsniff.reporting.finding import Finding
from testsniff.rules.checks.missing_assertion import MissingAssertionRule

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "missing_assertion"


def test_missing_assertion_rule_reports_top_level_test_without_assertion() -> None:
    findings = _analyze_fixture("positive_top_level.py")

    assert len(findings) == 1
    finding = findings[0]
    assert finding.rule_id == "TS003"
    assert finding.severity == "error"
    assert finding.confidence == "high"
    assert finding.line == 1


def test_missing_assertion_rule_reports_pytest_class_test_without_assertion() -> None:
    findings = _analyze_fixture("positive_pytest_class_method.py")

    assert len(findings) == 1
    assert findings[0].rule_id == "TS003"
    assert findings[0].line == 2


def test_missing_assertion_rule_reports_unittest_method_without_assertion() -> None:
    findings = _analyze_fixture("positive_unittest_method.py")

    assert len(findings) == 1
    assert findings[0].rule_id == "TS003"
    assert findings[0].line == 5


def test_missing_assertion_rule_ignores_bare_assertions() -> None:
    findings = _analyze_fixture("negative_assert.py")

    assert findings == []


def test_missing_assertion_rule_ignores_unittest_assertion_calls() -> None:
    findings = _analyze_fixture("negative_unittest_assertion.py")

    assert findings == []


def test_missing_assertion_rule_ignores_pytest_raises_calls() -> None:
    findings = _analyze_fixture("negative_pytest_raises.py")

    assert findings == []


def test_missing_assertion_rule_ignores_directly_imported_pytest_helpers() -> None:
    findings = _analyze_fixture("negative_pytest_raises_alias.py")

    assert findings == []


def test_missing_assertion_rule_ignores_pytest_fail_calls() -> None:
    findings = _analyze_fixture("negative_pytest_fail.py")

    assert findings == []


def _analyze_fixture(filename: str) -> list[Finding]:
    path = FIXTURES_DIR / filename
    module = ModuleContext.from_source(path, load_source(path))
    return MissingAssertionRule().analyze(module)
