from __future__ import annotations

from pathlib import Path

from testsniff.parser.loader import load_source
from testsniff.parser.module_context import ModuleContext
from testsniff.reporting.finding import Finding
from testsniff.rules.checks.magic_number_test import MagicNumberTestRule

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "magic_number_test"


def test_magic_number_test_rule_reports_bare_assert_literal_location() -> None:
    findings = _analyze_fixture("positive_bare_assert.py")

    assert len(findings) == 1
    finding = findings[0]
    assert finding.rule_id == "TS006"
    assert finding.severity == "warning"
    assert finding.confidence == "high"
    assert finding.line == 2
    assert finding.column == 21


def test_magic_number_test_rule_reports_negative_literal() -> None:
    findings = _analyze_fixture("positive_negative_literal.py")

    assert len(findings) == 1
    assert findings[0].rule_id == "TS006"
    assert findings[0].line == 2
    assert findings[0].column == 21


def test_magic_number_test_rule_reports_unittest_comparison_assertion() -> None:
    findings = _analyze_fixture("positive_unittest_assert_equal.py")

    assert len(findings) == 1
    assert findings[0].rule_id == "TS006"
    assert findings[0].line == 6
    assert findings[0].column == 33


def test_magic_number_test_rule_reports_unittest_condition_assertion() -> None:
    findings = _analyze_fixture("positive_unittest_assert_true.py")

    assert len(findings) == 1
    assert findings[0].rule_id == "TS006"
    assert findings[0].line == 6
    assert findings[0].column == 34


def test_magic_number_test_rule_ignores_small_integer_exclusions() -> None:
    findings = _analyze_fixture("negative_small_integer_literals.py")

    assert findings == []


def test_magic_number_test_rule_ignores_general_call_arguments() -> None:
    findings = _analyze_fixture("negative_general_call_argument.py")

    assert findings == []


def test_magic_number_test_rule_ignores_membership_assertions() -> None:
    findings = _analyze_fixture("negative_membership_assert.py")

    assert findings == []


def test_magic_number_test_rule_reports_each_literal_once() -> None:
    findings = _analyze_source(
        """
def test_example(value):
    assert 2 < value < 5
""".strip()
    )

    assert [(finding.line, finding.column) for finding in findings] == [(2, 12), (2, 24)]


def _analyze_fixture(filename: str) -> list[Finding]:
    path = FIXTURES_DIR / filename
    module = ModuleContext.from_source(path, load_source(path))
    return MagicNumberTestRule().analyze(module)


def _analyze_source(source: str) -> list[Finding]:
    module = ModuleContext.from_source(Path("tests/test_inline_magic_number.py"), source)
    return MagicNumberTestRule().analyze(module)
