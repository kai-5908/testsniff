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


def test_missing_assertion_rule_ignores_empty_tests_owned_by_ts001() -> None:
    findings = _analyze_fixture("negative_empty_test.py")

    assert findings == []


def test_missing_assertion_rule_reports_shadowed_pytest_module_alias() -> None:
    findings = _analyze_fixture("positive_shadowed_pytest_module_alias.py")

    assert len(findings) == 1
    assert findings[0].rule_id == "TS003"


def test_missing_assertion_rule_reports_shadowed_pytest_parameter() -> None:
    findings = _analyze_fixture("positive_shadowed_pytest_parameter.py")

    assert len(findings) == 1
    assert findings[0].rule_id == "TS003"


def test_missing_assertion_rule_reports_shadowed_direct_import_helper() -> None:
    findings = _analyze_fixture("positive_shadowed_direct_import_local.py")

    assert len(findings) == 1
    assert findings[0].rule_id == "TS003"


def test_missing_assertion_rule_reports_with_binder_shadowing() -> None:
    findings = _analyze_source(
        """
from pytest import raises

class Dummy:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def __call__(self, *args, **kwargs):
        return None

def test_example():
    with Dummy() as raises:
        raises(ValueError)
""".strip()
    )

    assert len(findings) == 1
    assert findings[0].rule_id == "TS003"


def test_missing_assertion_rule_reports_for_binder_shadowing() -> None:
    findings = _analyze_source(
        """
from pytest import raises

def helper(*args, **kwargs):
    return None

def test_example():
    for raises in (helper,):
        raises(ValueError)
""".strip()
    )

    assert len(findings) == 1
    assert findings[0].rule_id == "TS003"


def test_missing_assertion_rule_reports_except_binder_shadowing() -> None:
    findings = _analyze_source(
        """
from pytest import raises

def test_example():
    try:
        raise RuntimeError("boom")
    except RuntimeError as raises:
        raises(ValueError)
""".strip()
    )

    assert len(findings) == 1
    assert findings[0].rule_id == "TS003"


def test_missing_assertion_rule_recognizes_nested_import_before_pytest_helper_use() -> None:
    findings = _analyze_source(
        """
def test_example():
    if True:
        from pytest import raises
        with raises(ValueError):
            raise ValueError("boom")
""".strip()
    )

    assert findings == []


def test_missing_assertion_rule_propagates_if_block_import_to_later_statement() -> None:
    findings = _analyze_source(
        """
def test_example():
    if True:
        from pytest import raises
    with raises(ValueError):
        raise ValueError("boom")
""".strip()
    )

    assert findings == []


def test_missing_assertion_rule_propagates_with_block_import_to_later_statement() -> None:
    findings = _analyze_source(
        """
class Dummy:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

def test_example():
    with Dummy():
        from pytest import raises
    with raises(ValueError):
        raise ValueError("boom")
""".strip()
    )

    assert findings == []


def test_missing_assertion_rule_propagates_try_body_import_to_finally() -> None:
    findings = _analyze_source(
        """
def test_example():
    try:
        from pytest import raises
    finally:
        with raises(ValueError):
            raise ValueError("boom")
""".strip()
    )

    assert findings == []


def test_missing_assertion_rule_reports_match_capture_shadowing() -> None:
    findings = _analyze_source(
        """
from pytest import raises

def helper(*args, **kwargs):
    return None

def test_example():
    match helper:
        case raises:
            raises(ValueError)
""".strip()
    )

    assert len(findings) == 1
    assert findings[0].rule_id == "TS003"


def test_missing_assertion_rule_handles_deep_expressions_without_recursion_failure() -> None:
    expression = " + ".join(["value"] * 1200)
    module = ModuleContext.from_source(
        Path("tests/test_deep_expression.py"),
        f"def test_example():\n    {expression}\n",
    )

    findings = MissingAssertionRule().analyze(module)

    assert len(findings) == 1
    assert findings[0].rule_id == "TS003"


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


def test_missing_assertion_rule_ignores_pytest_warns_calls() -> None:
    findings = _analyze_source(
        """
import pytest

def test_example():
    with pytest.warns(UserWarning):
        raise UserWarning("boom")
""".strip()
    )

    assert findings == []


def _analyze_fixture(filename: str) -> list[Finding]:
    path = FIXTURES_DIR / filename
    module = ModuleContext.from_source(path, load_source(path))
    return MissingAssertionRule().analyze(module)


def _analyze_source(source: str) -> list[Finding]:
    module = ModuleContext.from_source(Path("tests/test_inline_missing_assertion.py"), source)
    return MissingAssertionRule().analyze(module)
