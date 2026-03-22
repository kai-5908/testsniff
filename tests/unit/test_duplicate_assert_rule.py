from __future__ import annotations

from pathlib import Path

from testsniff.parser.loader import load_source
from testsniff.parser.module_context import ModuleContext
from testsniff.reporting.finding import Finding
from testsniff.rules.checks.duplicate_assert import DuplicateAssertRule

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "duplicate_assert"


def test_duplicate_assert_rule_reports_top_level_duplicate_bare_assertion() -> None:
    findings = _analyze_fixture("positive_duplicate_assert.py")

    assert len(findings) == 1
    finding = findings[0]
    assert finding.rule_id == "TS005"
    assert finding.severity == "error"
    assert finding.confidence == "high"
    assert finding.line == 1


def test_duplicate_assert_rule_normalizes_parenthesized_assertions() -> None:
    findings = _analyze_fixture("positive_duplicate_assert_parenthesized.py")

    assert len(findings) == 1
    assert findings[0].rule_id == "TS005"


def test_duplicate_assert_rule_reports_duplicate_unittest_assertion() -> None:
    findings = _analyze_fixture("positive_duplicate_unittest_assertion.py")

    assert len(findings) == 1
    assert findings[0].rule_id == "TS005"
    assert findings[0].line == 5


def test_duplicate_assert_rule_ignores_different_bare_assertions() -> None:
    findings = _analyze_fixture("negative_distinct_assertions.py")

    assert findings == []


def test_duplicate_assert_rule_ignores_different_unittest_assertions() -> None:
    findings = _analyze_fixture("negative_distinct_unittest_assertions.py")

    assert findings == []


def test_duplicate_assert_rule_ignores_mutually_exclusive_duplicate_assertions() -> None:
    findings = _analyze_source(
        """
def test_example(value, flag):
    if flag:
        assert value == 1
    else:
        assert value == 1
""".strip()
    )

    assert findings == []


def test_duplicate_assert_rule_reports_duplicate_after_static_true_branch() -> None:
    findings = _analyze_source(
        """
def test_example(value):
    if True:
        assert value == 1
    assert value == 1
""".strip()
    )

    assert len(findings) == 1
    assert findings[0].rule_id == "TS005"


def test_duplicate_assert_rule_ignores_duplicate_in_finally_when_not_guaranteed() -> None:
    findings = _analyze_source(
        """
def test_example(value, should_fail):
    try:
        if should_fail:
            raise RuntimeError()
        assert value == 1
    except RuntimeError:
        pass
    finally:
        assert value == 1
""".strip()
    )

    assert findings == []


def test_duplicate_assert_rule_reports_duplicate_across_try_except_after_explicit_raise() -> None:
    findings = _analyze_source(
        """
def test_example(value):
    try:
        assert value == 1
        raise RuntimeError()
    except RuntimeError:
        assert value == 1
""".strip()
    )

    assert len(findings) == 1
    assert findings[0].rule_id == "TS005"


def test_duplicate_assert_rule_ignores_non_exhaustive_match_without_catch_all() -> None:
    findings = _analyze_source(
        """
def test_example(value):
    match value:
        case 1:
            assert value == 1
    assert value == 1
""".strip()
    )

    assert findings == []


def test_duplicate_assert_rule_treats_unittest_messages_consistently() -> None:
    keyword_findings = _analyze_source(
        """
import unittest

class TestExample(unittest.TestCase):
    def test_example(self, value):
        self.assertEqual(value, 1, msg="a")
        self.assertEqual(value, 1, msg="b")
""".strip()
    )
    positional_findings = _analyze_source(
        """
import unittest

class TestExample(unittest.TestCase):
    def test_example(self, value):
        self.assertEqual(value, 1, "a")
        self.assertEqual(value, 1, "b")
""".strip()
    )

    assert keyword_findings == []
    assert positional_findings == []


def test_duplicate_assert_rule_handles_deep_assertions_without_recursion_failure() -> None:
    expression = "not " * 1200 + "value"
    findings = _analyze_source(
        f"def test_example(value):\n    assert {expression}\n    assert {expression}\n"
    )

    assert len(findings) == 1
    assert findings[0].rule_id == "TS005"


def test_duplicate_assert_rule_ignores_unreachable_assert_after_terminating_if_branches() -> None:
    findings = _analyze_source(
        """
def test_example(value, flag):
    if flag:
        assert value == 1
        return
    else:
        assert value == 1
        return
    assert value == 1
""".strip()
    )

    assert findings == []


def test_duplicate_assert_rule_ignores_unreachable_assert_after_terminating_match_cases() -> None:
    findings = _analyze_source(
        """
def test_example(value):
    match value:
        case 1:
            assert value == 1
            return
        case _:
            assert value == 1
            return
    assert value == 1
""".strip()
    )

    assert findings == []


def test_duplicate_assert_rule_ignores_unreachable_assert_after_terminating_try_finally() -> None:
    findings = _analyze_source(
        """
def test_example(value, flag):
    try:
        if flag:
            assert value == 1
            return
        else:
            assert value == 1
            return
    finally:
        pass
    assert value == 1
""".strip()
    )

    assert findings == []


def _analyze_fixture(filename: str) -> list[Finding]:
    path = FIXTURES_DIR / filename
    module = ModuleContext.from_source(path, load_source(path))
    return DuplicateAssertRule().analyze(module)


def _analyze_source(source: str) -> list[Finding]:
    module = ModuleContext.from_source(Path("tests/test_inline_duplicate_assert.py"), source)
    return DuplicateAssertRule().analyze(module)
