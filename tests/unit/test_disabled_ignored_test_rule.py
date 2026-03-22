from __future__ import annotations

from pathlib import Path

from testsniff.parser.loader import load_source
from testsniff.parser.module_context import ModuleContext
from testsniff.reporting.finding import Finding
from testsniff.rules.checks.disabled_ignored_test import DisabledIgnoredTestRule

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "disabled_ignored_test"


def test_disabled_ignored_rule_reports_pytest_skip_decorator() -> None:
    findings = _analyze_fixture("positive_pytest_skip.py")

    assert len(findings) == 1
    finding = findings[0]
    assert finding.rule_id == "TS004"
    assert finding.severity == "warning"
    assert finding.confidence == "high"
    assert finding.line == 5


def test_disabled_ignored_rule_reports_pytest_skipif_module_alias() -> None:
    findings = _analyze_fixture("positive_pytest_skipif_alias.py")

    assert len(findings) == 1
    assert findings[0].rule_id == "TS004"
    assert findings[0].line == 5


def test_disabled_ignored_rule_reports_unittest_skip_direct_import_alias() -> None:
    findings = _analyze_fixture("positive_unittest_skip_import_alias.py")

    assert len(findings) == 1
    assert findings[0].rule_id == "TS004"
    assert findings[0].line == 7


def test_disabled_ignored_rule_reports_unittest_skipif_case_module_alias() -> None:
    findings = _analyze_fixture("positive_unittest_skipif_case_module.py")

    assert len(findings) == 1
    assert findings[0].rule_id == "TS004"
    assert findings[0].line == 7


def test_disabled_ignored_rule_reports_unittest_skipunless_module_alias() -> None:
    findings = _analyze_fixture("positive_unittest_skipunless_module_alias.py")

    assert len(findings) == 1
    assert findings[0].rule_id == "TS004"
    assert findings[0].line == 6


def test_disabled_ignored_rule_expands_class_level_pytest_skip_to_each_method() -> None:
    findings = _analyze_fixture("positive_class_level_pytest_skip.py")

    assert len(findings) == 2
    assert [finding.line for finding in findings] == [6, 9]
    assert all(finding.rule_id == "TS004" for finding in findings)
    assert all(finding.headline == findings[0].headline for finding in findings)
    assert all(finding.why == findings[0].why for finding in findings)
    assert all(finding.fix == findings[0].fix for finding in findings)


def test_disabled_ignored_rule_ignores_pytest_mark_direct_import() -> None:
    findings = _analyze_fixture("negative_pytest_mark_direct_import.py")

    assert findings == []


def test_disabled_ignored_rule_ignores_pytest_mark_direct_import_alias() -> None:
    findings = _analyze_source(
        """
from pytest import mark as pt_mark

@pt_mark.skip(reason="temporarily disabled")
def test_example():
    assert True
""".strip()
    )

    assert findings == []


def test_disabled_ignored_rule_ignores_expected_failure() -> None:
    findings = _analyze_fixture("negative_expected_failure.py")

    assert findings == []


def test_disabled_ignored_rule_ignores_runtime_pytest_skip_calls() -> None:
    findings = _analyze_fixture("negative_runtime_pytest_skip.py")

    assert findings == []


def test_disabled_ignored_rule_ignores_unrelated_decorators() -> None:
    findings = _analyze_fixture("negative_unrelated_decorator.py")

    assert findings == []


def _analyze_fixture(filename: str) -> list[Finding]:
    path = FIXTURES_DIR / filename
    module = ModuleContext.from_source(path, load_source(path))
    return DisabledIgnoredTestRule().analyze(module)


def _analyze_source(source: str) -> list[Finding]:
    module = ModuleContext.from_source(Path("tests/test_inline_disabled_ignored.py"), source)
    return DisabledIgnoredTestRule().analyze(module)
