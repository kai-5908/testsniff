from __future__ import annotations

import ast
from pathlib import Path

import pytest

from testsniff.parser.loader import load_source
from testsniff.parser.module_context import ModuleContext
from testsniff.reporting.finding import Finding
from testsniff.rules.checks import magic_number_test
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


def test_magic_number_test_rule_handles_top_level_test_without_arguments() -> None:
    findings = _analyze_source(
        """
def test_example():
    assert helper() == 200
""".strip()
    )

    assert len(findings) == 1
    assert findings[0].line == 2
    assert findings[0].column == 24


def test_magic_number_test_rule_deduplicates_same_literal_location(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = ModuleContext.from_source(
        Path("tests/test_magic_number_dedup.py"),
        "def test_example():\n    assert True\n",
    )
    literal = ast.parse("200", mode="eval").body

    monkeypatch.setattr(
        magic_number_test,
        "_iter_magic_number_literals",
        lambda target: [literal, literal],
    )

    findings = MagicNumberTestRule().analyze(module)

    assert len(findings) == 1
    assert findings[0].line == 1
    assert findings[0].column == 1


def test_magic_number_test_rule_scans_nested_blocks() -> None:
    findings = _analyze_source(
        """
def test_example(value):
    if value:
        assert value == 200
    else:
        with helper():
            assert value == 300
""".strip()
    )

    assert [(finding.line, finding.column) for finding in findings] == [(3, 25), (6, 29)]


@pytest.mark.parametrize(
    ("source", "expected_count"),
    [
        ("count: int\n", 0),
        ("count += 2\n", 1),
        ("return value\n", 1),
        ("raise RuntimeError(2) from exc\n", 2),
        ("if flag:\n    pass\n", 1),
        ("for item in range(2):\n    pass\n", 1),
        ("with helper(2) as value:\n    pass\n", 1),
        ("match value:\n    case 2:\n        pass\n", 1),
        ("pass\n", 0),
    ],
)
def test_magic_number_statement_header_expression_coverage(
    source: str,
    expected_count: int,
) -> None:
    statement = ast.parse(source).body[0]

    assert (
        len(magic_number_test._iter_statement_header_expressions(statement))
        == expected_count
    )


@pytest.mark.parametrize(
    ("source", "expected_count"),
    [
        ("if flag:\n    pass\nelse:\n    pass\n", 2),
        ("with helper():\n    pass\n", 1),
        (
            "try:\n    pass\nexcept RuntimeError:\n    pass\nelse:\n    pass\nfinally:\n    pass\n",
            4,
        ),
        ("match value:\n    case 1:\n        pass\n    case _:\n        pass\n", 2),
        ("pass\n", 0),
    ],
)
def test_magic_number_nested_statement_block_coverage(
    source: str,
    expected_count: int,
) -> None:
    statement = ast.parse(source).body[0]

    assert len(magic_number_test._iter_nested_statement_blocks(statement)) == expected_count


def test_magic_number_expression_helper_skips_lambda() -> None:
    expression = ast.parse("(lambda value: value == 200)", mode="eval").body

    assert (
        magic_number_test._iter_expression_magic_number_literals(
            expression,
            unittest_receiver_name="self",
        )
        == []
    )


def test_magic_number_unittest_condition_assertion_without_argument_returns_no_literals() -> None:
    expression = ast.parse("self.assertTrue()", mode="eval").body

    assert magic_number_test._iter_unittest_call_magic_number_literals(
        expression,
        unittest_receiver_name="self",
    ) == []


def test_magic_number_unittest_unsupported_method_returns_no_literals() -> None:
    expression = ast.parse("self.assertIn(value, [2])", mode="eval").body

    assert magic_number_test._iter_unittest_call_magic_number_literals(
        expression,
        unittest_receiver_name="self",
    ) == []


def test_magic_number_unittest_binary_value_expressions_include_supported_keywords_only() -> None:
    expression = ast.parse(
        'self.assertEqual(actual=value, expected=200, msg="nope")',
        mode="eval",
    ).body

    values = magic_number_test._iter_unittest_binary_value_expressions(expression)

    assert len(values) == 2
    assert [ast.unparse(value) for value in values] == ["value", "200"]


def test_magic_number_find_keyword_argument_returns_match_or_none() -> None:
    expression = ast.parse("self.assertTrue(expr=value == 200)", mode="eval").body

    matched = magic_number_test._find_keyword_argument(expression, "expr")
    missing = magic_number_test._find_keyword_argument(expression, "missing")

    assert matched is not None
    assert ast.unparse(matched) == "value == 200"
    assert missing is None


def test_magic_number_compare_helper_skips_lambda_children() -> None:
    expression = ast.parse("(lambda: 200 == 300)", mode="eval").body

    assert magic_number_test._iter_compare_magic_number_literals(expression) == []


def test_magic_number_extract_literal_rejects_non_expression_nodes() -> None:
    node = ast.parse("pass").body[0]

    assert magic_number_test._extract_magic_number_literal(node) is None


def test_magic_number_numeric_literal_value_handles_unary_and_invalid_values() -> None:
    assert magic_number_test._numeric_literal_value(ast.parse("+2", mode="eval").body) == 2
    assert magic_number_test._numeric_literal_value(ast.parse("-value", mode="eval").body) is None
    assert magic_number_test._numeric_literal_value(ast.parse('-"x"', mode="eval").body) is None


def test_magic_number_coerce_numeric_value_rejects_non_numeric_values() -> None:
    assert magic_number_test._coerce_numeric_value("x") is None


def test_magic_number_resolve_unittest_assertion_method_name_covers_rejections() -> None:
    plain_call = ast.parse("helper(2)", mode="eval").body
    foreign_call = ast.parse("other.assertEqual(value, 2)", mode="eval").body
    unsupported_call = ast.parse("self.assertIn(value, [2])", mode="eval").body
    non_assert_method = ast.parse("self.helper(value, 2)", mode="eval").body

    assert (
        magic_number_test._resolve_unittest_assertion_method_name(
            plain_call,
            unittest_receiver_name="self",
        )
        is None
    )
    assert (
        magic_number_test._resolve_unittest_assertion_method_name(
            foreign_call,
            unittest_receiver_name="self",
        )
        is None
    )
    assert (
        magic_number_test._resolve_unittest_assertion_method_name(
            unsupported_call,
            unittest_receiver_name="self",
        )
        == "assertIn"
    )
    assert (
        magic_number_test._resolve_unittest_assertion_method_name(
            non_assert_method,
            unittest_receiver_name="self",
        )
        is None
    )


def _analyze_fixture(filename: str) -> list[Finding]:
    path = FIXTURES_DIR / filename
    module = ModuleContext.from_source(path, load_source(path))
    return MagicNumberTestRule().analyze(module)


def _analyze_source(source: str) -> list[Finding]:
    module = ModuleContext.from_source(Path("tests/test_inline_magic_number.py"), source)
    return MagicNumberTestRule().analyze(module)
