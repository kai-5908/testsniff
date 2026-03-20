from __future__ import annotations

from pathlib import Path

from testsniff.parser.loader import load_source
from testsniff.parser.module_context import ModuleContext
from testsniff.reporting.finding import Finding
from testsniff.rules.checks.comments_only_test import CommentsOnlyTestRule

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "comments_only_test"


def test_comments_only_rule_reports_docstring_with_comments() -> None:
    findings = _analyze_fixture("positive_docstring_with_comments.py")

    assert len(findings) == 1
    finding = findings[0]
    assert finding.rule_id == "TS002"
    assert finding.severity == "error"
    assert finding.confidence == "high"
    assert finding.line == 1


def test_comments_only_rule_reports_unittest_method() -> None:
    findings = _analyze_fixture("positive_unittest_method.py")

    assert len(findings) == 1
    finding = findings[0]
    assert finding.rule_id == "TS002"
    assert finding.line == 5


def test_comments_only_rule_reports_one_line_placeholder() -> None:
    findings = _analyze_fixture("positive_one_line_docstring_with_comment.py")

    assert len(findings) == 1
    assert findings[0].rule_id == "TS002"


def test_comments_only_rule_ignores_docstring_only_tests() -> None:
    findings = _analyze_fixture("negative_docstring_only.py")

    assert findings == []


def test_comments_only_rule_ignores_tests_with_pass() -> None:
    findings = _analyze_fixture("negative_pass_with_comment.py")

    assert findings == []


def test_comments_only_rule_ignores_tests_with_real_assertions() -> None:
    findings = _analyze_fixture("negative_assert_with_comment.py")

    assert findings == []


def test_comments_only_rule_ignores_non_test_helpers() -> None:
    findings = _analyze_fixture("negative_helper_docstring_with_comment.py")

    assert findings == []


def _analyze_fixture(filename: str) -> list[Finding]:
    path = FIXTURES_DIR / filename
    module = ModuleContext.from_source(path, load_source(path))
    return CommentsOnlyTestRule().analyze(module)
