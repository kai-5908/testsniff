from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import cast

from testsniff.config.types import Confidence, Severity
from testsniff.docs.rule_metadata import MAGIC_NUMBER_TEST
from testsniff.parser.ast_index import TestTarget
from testsniff.parser.module_context import ModuleContext
from testsniff.reporting.finding import Finding
from testsniff.rules.checks._function_body import is_effectively_empty, iter_executable_body

_BINARY_ASSERTION_METHODS = frozenset(
    {
        "assertEqual",
        "assertNotEqual",
        "assertGreater",
        "assertGreaterEqual",
        "assertLess",
        "assertLessEqual",
        "assertAlmostEqual",
        "assertNotAlmostEqual",
    }
)
_CONDITION_ASSERTION_METHODS = frozenset({"assertTrue", "assertFalse"})
_SUPPORTED_COMPARE_OPERATORS = (
    ast.Eq,
    ast.NotEq,
    ast.Lt,
    ast.LtE,
    ast.Gt,
    ast.GtE,
)
_BINARY_ASSERTION_KEYWORDS = frozenset(
    {"a", "actual", "b", "expected", "expr1", "expr2", "first", "second"}
)


@dataclass(slots=True)
class MagicNumberTestRule:
    rule_id: str = MAGIC_NUMBER_TEST.rule_id
    default_severity: Severity = MAGIC_NUMBER_TEST.default_severity
    default_confidence: Confidence = MAGIC_NUMBER_TEST.default_confidence

    def analyze(self, module: ModuleContext) -> list[Finding]:
        findings: list[Finding] = []

        for target in module.index.test_targets:
            if is_effectively_empty(target.node):
                continue

            seen_locations: set[tuple[int, int]] = set()
            for literal in _iter_magic_number_literals(target):
                location = (literal.lineno, literal.col_offset)
                if location in seen_locations:
                    continue
                seen_locations.add(location)
                findings.append(
                    Finding(
                        rule_id=self.rule_id,
                        headline=MAGIC_NUMBER_TEST.headline,
                        severity=self.default_severity,
                        confidence=self.default_confidence,
                        path=str(module.path),
                        line=literal.lineno,
                        column=literal.col_offset + 1,
                        why=MAGIC_NUMBER_TEST.why,
                        fix=MAGIC_NUMBER_TEST.fix,
                        example=MAGIC_NUMBER_TEST.example,
                        references=MAGIC_NUMBER_TEST.references,
                    )
                )

        return findings


def _iter_magic_number_literals(target: TestTarget) -> list[ast.expr]:
    receiver_name = _get_instance_receiver_name(target)
    literals: list[ast.expr] = []

    for statement in iter_executable_body(target.node):
        literals.extend(
            _iter_statement_magic_number_literals(
                statement,
                unittest_receiver_name=receiver_name if target.style == "unittest" else None,
            )
        )

    return literals


def _get_instance_receiver_name(target: TestTarget) -> str | None:
    arguments = target.node.args.posonlyargs + target.node.args.args
    if not arguments:
        return None
    return arguments[0].arg if target.class_name is not None else None


def _iter_statement_magic_number_literals(
    statement: ast.stmt,
    *,
    unittest_receiver_name: str | None,
) -> list[ast.expr]:
    literals: list[ast.expr] = []

    if isinstance(statement, ast.Assert):
        literals.extend(_iter_compare_magic_number_literals(statement.test))
    else:
        for expression in _iter_statement_header_expressions(statement):
            literals.extend(
                _iter_expression_magic_number_literals(
                    expression,
                    unittest_receiver_name=unittest_receiver_name,
                )
            )

    for block in _iter_nested_statement_blocks(statement):
        for nested_statement in block:
            literals.extend(
                _iter_statement_magic_number_literals(
                    nested_statement,
                    unittest_receiver_name=unittest_receiver_name,
                )
            )

    return literals


def _iter_statement_header_expressions(statement: ast.stmt) -> tuple[ast.AST, ...]:
    if isinstance(statement, ast.Expr):
        return (statement.value,)
    if isinstance(statement, ast.Assign):
        return (statement.value,)
    if isinstance(statement, ast.AnnAssign):
        return (statement.value,) if statement.value is not None else ()
    if isinstance(statement, ast.AugAssign):
        return (statement.value,)
    if isinstance(statement, ast.Return):
        return (statement.value,) if statement.value is not None else ()
    if isinstance(statement, ast.Raise):
        expressions: list[ast.AST] = []
        if statement.exc is not None:
            expressions.append(statement.exc)
        if statement.cause is not None:
            expressions.append(statement.cause)
        return tuple(expressions)
    if isinstance(statement, ast.If | ast.While):
        return (statement.test,)
    if isinstance(statement, ast.For | ast.AsyncFor):
        return (statement.iter,)
    if isinstance(statement, ast.With | ast.AsyncWith):
        return tuple(item.context_expr for item in statement.items)
    if isinstance(statement, ast.Match):
        return (statement.subject,)
    return ()


def _iter_nested_statement_blocks(statement: ast.stmt) -> tuple[tuple[ast.stmt, ...], ...]:
    if isinstance(statement, ast.If | ast.For | ast.AsyncFor | ast.While):
        return (tuple(statement.body), tuple(statement.orelse))
    if isinstance(statement, ast.With | ast.AsyncWith):
        return (tuple(statement.body),)
    if isinstance(statement, ast.Try):
        handler_bodies = tuple(tuple(handler.body) for handler in statement.handlers)
        return (
            tuple(statement.body),
            tuple(statement.orelse),
            tuple(statement.finalbody),
            *handler_bodies,
        )
    if isinstance(statement, ast.Match):
        return tuple(tuple(case.body) for case in statement.cases)
    return ()


def _iter_expression_magic_number_literals(
    expression: ast.AST,
    *,
    unittest_receiver_name: str | None,
) -> list[ast.expr]:
    literals: list[ast.expr] = []
    stack: list[ast.AST] = [expression]

    while stack:
        node = stack.pop()
        if isinstance(node, ast.Call):
            literals.extend(
                _iter_unittest_call_magic_number_literals(
                    node,
                    unittest_receiver_name=unittest_receiver_name,
                )
            )
            if _is_supported_unittest_assertion_call(node, unittest_receiver_name):
                continue
        if isinstance(node, ast.Lambda):
            continue
        children = list(ast.iter_child_nodes(node))
        for child in reversed(children):
            stack.append(child)

    return literals


def _iter_unittest_call_magic_number_literals(
    call: ast.Call,
    *,
    unittest_receiver_name: str | None,
) -> list[ast.expr]:
    method_name = _resolve_unittest_assertion_method_name(call, unittest_receiver_name)
    if method_name is None:
        return []
    if method_name in _CONDITION_ASSERTION_METHODS:
        condition = call.args[0] if call.args else _find_keyword_argument(call, "expr")
        if condition is None:
            return []
        return _iter_compare_magic_number_literals(condition)

    if method_name in _BINARY_ASSERTION_METHODS:
        literals: list[ast.expr] = []
        for expression in _iter_unittest_binary_value_expressions(call):
            literal = _extract_magic_number_literal(expression)
            if literal is not None:
                literals.append(literal)
        return literals

    return []


def _iter_unittest_binary_value_expressions(call: ast.Call) -> list[ast.expr]:
    expressions = list(call.args[:2])
    for keyword in call.keywords:
        if keyword.arg in _BINARY_ASSERTION_KEYWORDS:
            expressions.append(keyword.value)
    return expressions


def _find_keyword_argument(call: ast.Call, name: str) -> ast.expr | None:
    for keyword in call.keywords:
        if keyword.arg == name:
            return keyword.value
    return None


def _iter_compare_magic_number_literals(expression: ast.AST) -> list[ast.expr]:
    literals: list[ast.expr] = []
    stack: list[ast.AST] = [expression]

    while stack:
        node = stack.pop()
        if isinstance(node, ast.Compare) and all(
            isinstance(operator, _SUPPORTED_COMPARE_OPERATORS)
            for operator in node.ops
        ):
            operands = [node.left, *node.comparators]
            for operand in operands:
                literal = _extract_magic_number_literal(operand)
                if literal is not None:
                    literals.append(literal)
        if isinstance(node, ast.Lambda):
            continue
        children = list(ast.iter_child_nodes(node))
        for child in reversed(children):
            stack.append(child)

    return literals


def _extract_magic_number_literal(expression: ast.AST) -> ast.expr | None:
    if not isinstance(expression, ast.expr):
        return None

    value = _numeric_literal_value(expression)
    if value is None or value in {0, 1, -1}:
        return None
    return expression


def _numeric_literal_value(expression: ast.expr) -> int | float | complex | None:
    if isinstance(expression, ast.Constant):
        return _coerce_numeric_value(expression.value)

    if not isinstance(expression, ast.UnaryOp) or not isinstance(
        expression.op,
        (ast.UAdd, ast.USub),
    ):
        return None
    if not isinstance(expression.operand, ast.Constant):
        return None
    operand_value = _coerce_numeric_value(expression.operand.value)
    if operand_value is None:
        return None

    if isinstance(expression.op, ast.UAdd):
        return operand_value
    return -operand_value


def _coerce_numeric_value(value: object) -> int | float | complex | None:
    if type(value) not in {int, float, complex}:
        return None
    return cast(int | float | complex, value)


def _is_supported_unittest_assertion_call(
    call: ast.Call,
    unittest_receiver_name: str | None,
) -> bool:
    method_name = _resolve_unittest_assertion_method_name(call, unittest_receiver_name)
    return method_name in _BINARY_ASSERTION_METHODS | _CONDITION_ASSERTION_METHODS


def _resolve_unittest_assertion_method_name(
    call: ast.Call,
    unittest_receiver_name: str | None,
) -> str | None:
    if unittest_receiver_name is None:
        return None
    if not isinstance(call.func, ast.Attribute):
        return None
    if not isinstance(call.func.value, ast.Name) or call.func.value.id != unittest_receiver_name:
        return None
    method_name = call.func.attr
    if method_name.startswith("assert"):
        return method_name
    return None
