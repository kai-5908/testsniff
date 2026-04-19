from __future__ import annotations

from pathlib import Path

from testsniff.parser.module_context import ModuleContext
from testsniff.rules.checks.conditional_logic import ConditionalLogicRule

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "conditional_logic"


def test_conditional_logic_rule_reports_pytest_test_with_if() -> None:
    findings = _analyze_fixture("positive_pytest_if.py")

    assert len(findings) == 1
    finding = findings[0]
    assert finding.rule_id == "TS007"
    assert finding.severity == "warning"
    assert finding.confidence == "high"
    assert finding.line == 1


def test_conditional_logic_rule_reports_pytest_test_with_elif() -> None:
    findings = _analyze_fixture("positive_pytest_elif.py")

    assert len(findings) == 1
    assert findings[0].rule_id == "TS007"
    assert findings[0].line == 1


def test_conditional_logic_rule_reports_unittest_method_with_if() -> None:
    findings = _analyze_fixture("positive_unittest_if.py")

    assert len(findings) == 1
    assert findings[0].rule_id == "TS007"
    assert findings[0].line == 5


def test_conditional_logic_rule_ignores_tests_without_statement_level_branch() -> None:
    findings = _analyze_fixture("negative_no_branch.py")

    assert findings == []


def test_conditional_logic_rule_ignores_nested_helper_branch() -> None:
    findings = _analyze_fixture("negative_nested_helper_if.py")

    assert findings == []


def test_conditional_logic_rule_ignores_if_expression() -> None:
    findings = _analyze_fixture("negative_if_expression.py")

    assert findings == []


def test_conditional_logic_rule_ignores_match_statement() -> None:
    findings = _analyze_fixture("negative_match.py")

    assert findings == []


def test_conditional_logic_rule_ignores_comprehension_filter() -> None:
    findings = _analyze_fixture("negative_comprehension_if.py")

    assert findings == []


def test_conditional_logic_rule_reports_if_nested_inside_try() -> None:
    findings = _analyze_source(
        """
def test_example(flag):
    try:
        if flag:
            assert True
    finally:
        assert True
""".strip()
    )

    assert len(findings) == 1
    assert findings[0].rule_id == "TS007"


def test_conditional_logic_rule_reports_if_nested_inside_with_block() -> None:
    findings = _analyze_source(
        """
class Dummy:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

def test_example(flag):
    with Dummy():
        if flag:
            assert True
""".strip()
    )

    assert len(findings) == 1
    assert findings[0].rule_id == "TS007"


def test_conditional_logic_rule_reports_if_nested_inside_loop_else() -> None:
    findings = _analyze_source(
        """
def test_example(values, flag):
    for value in values:
        assert value is not None
    else:
        if flag:
            assert True
""".strip()
    )

    assert len(findings) == 1
    assert findings[0].rule_id == "TS007"


def test_conditional_logic_rule_reports_if_nested_inside_except_handler() -> None:
    findings = _analyze_source(
        """
def test_example(flag):
    try:
        raise RuntimeError("boom")
    except RuntimeError:
        if flag:
            assert True
""".strip()
    )

    assert len(findings) == 1
    assert findings[0].rule_id == "TS007"


def test_conditional_logic_rule_reports_if_nested_inside_except_star_handler() -> None:
    findings = _analyze_source(
        """
def test_example(flag):
    try:
        raise ValueErrorGroup("boom", [ValueError("x")])
    except* ValueError:
        if flag:
            assert True
""".strip()
    )

    assert len(findings) == 1
    assert findings[0].rule_id == "TS007"


def test_conditional_logic_rule_reports_if_nested_inside_try_finally_only() -> None:
    findings = _analyze_source(
        """
def test_example(flag):
    try:
        assert True
    finally:
        if flag:
            assert True
""".strip()
    )

    assert len(findings) == 1
    assert findings[0].rule_id == "TS007"


def test_conditional_logic_rule_reports_if_nested_inside_match_case_body() -> None:
    findings = _analyze_source(
        """
def test_example(value):
    match value:
        case "a":
            if value:
                assert True
        case _:
            assert True
""".strip()
    )

    assert len(findings) == 1
    assert findings[0].rule_id == "TS007"


def _analyze_fixture(filename: str):
    return _analyze_source((FIXTURES_DIR / filename).read_text())


def _analyze_source(source: str):
    module = ModuleContext.from_source(Path("tests/test_conditional_logic.py"), source)
    return ConditionalLogicRule().analyze(module)
