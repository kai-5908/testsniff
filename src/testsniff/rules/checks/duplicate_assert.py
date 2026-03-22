from __future__ import annotations

import ast
from dataclasses import dataclass

from testsniff.config.types import Confidence, Severity
from testsniff.docs.rule_metadata import DUPLICATE_ASSERT
from testsniff.parser.ast_index import TestTarget
from testsniff.parser.module_context import ModuleContext
from testsniff.reporting.finding import Finding
from testsniff.rules.checks._function_body import is_effectively_empty, iter_executable_body

type _NormalizedValue = object
type _AssertionKey = tuple[str, _NormalizedValue]
_IGNORED_NORMALIZED_FIELDS = {
    "col_offset",
    "ctx",
    "end_col_offset",
    "end_lineno",
    "lineno",
    "type_comment",
}


@dataclass(slots=True)
class DuplicateAssertRule:
    rule_id: str = DUPLICATE_ASSERT.rule_id
    default_severity: Severity = DUPLICATE_ASSERT.default_severity
    default_confidence: Confidence = DUPLICATE_ASSERT.default_confidence

    def analyze(self, module: ModuleContext) -> list[Finding]:
        findings: list[Finding] = []

        for target in module.index.test_targets:
            if is_effectively_empty(target.node):
                continue
            if not _has_duplicate_assertion(target):
                continue

            function = target.node
            findings.append(
                Finding(
                    rule_id=self.rule_id,
                    headline=DUPLICATE_ASSERT.headline,
                    severity=self.default_severity,
                    confidence=self.default_confidence,
                    path=str(module.path),
                    line=function.lineno,
                    column=function.col_offset + 1,
                    why=DUPLICATE_ASSERT.why,
                    fix=DUPLICATE_ASSERT.fix,
                    example=DUPLICATE_ASSERT.example,
                    references=DUPLICATE_ASSERT.references,
                )
            )

        return findings


def _has_duplicate_assertion(target: TestTarget) -> bool:
    seen_assertions: set[_AssertionKey] = set()
    receiver_name = _get_instance_receiver_name(target)
    return _block_has_duplicate_assertion(
        iter_executable_body(target.node),
        seen_assertions=seen_assertions,
        unittest_receiver_name=receiver_name if target.style == "unittest" else None,
    )


def _get_instance_receiver_name(target: TestTarget) -> str | None:
    arguments = target.node.args.posonlyargs + target.node.args.args
    if not arguments:
        return None
    return arguments[0].arg if target.class_name is not None else None


def _block_has_duplicate_assertion(
    statements: tuple[ast.stmt, ...] | list[ast.stmt],
    *,
    seen_assertions: set[_AssertionKey],
    unittest_receiver_name: str | None,
) -> bool:
    for statement in statements:
        if _statement_has_duplicate_assertion(
            statement,
            seen_assertions=seen_assertions,
            unittest_receiver_name=unittest_receiver_name,
        ):
            return True
    return False


def _statement_has_duplicate_assertion(
    statement: ast.stmt,
    *,
    seen_assertions: set[_AssertionKey],
    unittest_receiver_name: str | None,
) -> bool:
    if isinstance(statement, ast.Assert):
        return _record_assertion_key(
            _normalize_bare_assert(statement),
            seen_assertions=seen_assertions,
        )

    if _record_statement_header_assertions(
        statement,
        seen_assertions=seen_assertions,
        unittest_receiver_name=unittest_receiver_name,
    ):
        return True

    if isinstance(statement, ast.With | ast.AsyncWith):
        body_seen = set(seen_assertions)
        if _block_has_duplicate_assertion(
            statement.body,
            seen_assertions=body_seen,
            unittest_receiver_name=unittest_receiver_name,
        ):
            return True
        _overwrite_seen_assertions(seen_assertions, body_seen)
        return False

    if isinstance(statement, ast.If):
        body_seen = set(seen_assertions)
        if _block_has_duplicate_assertion(
            statement.body,
            seen_assertions=body_seen,
            unittest_receiver_name=unittest_receiver_name,
        ):
            return True
        else_seen = set(seen_assertions)
        if _block_has_duplicate_assertion(
            statement.orelse,
            seen_assertions=else_seen,
            unittest_receiver_name=unittest_receiver_name,
        ):
            return True
        if _is_static_truthy(statement.test):
            _overwrite_seen_assertions(seen_assertions, body_seen)
        elif _is_static_falsy(statement.test):
            _overwrite_seen_assertions(seen_assertions, else_seen)
        else:
            _overwrite_seen_assertions(seen_assertions, body_seen & else_seen)
        return False

    if isinstance(statement, ast.For | ast.AsyncFor):
        body_seen = set(seen_assertions)
        if _block_has_duplicate_assertion(
            statement.body,
            seen_assertions=body_seen,
            unittest_receiver_name=unittest_receiver_name,
        ):
            return True
        orelse_seen = set(seen_assertions)
        if _block_has_duplicate_assertion(
            statement.orelse,
            seen_assertions=orelse_seen,
            unittest_receiver_name=unittest_receiver_name,
        ):
            return True
        return False

    if isinstance(statement, ast.While):
        body_seen = set(seen_assertions)
        if _block_has_duplicate_assertion(
            statement.body,
            seen_assertions=body_seen,
            unittest_receiver_name=unittest_receiver_name,
        ):
            return True
        else_seen = set(seen_assertions)
        if _block_has_duplicate_assertion(
            statement.orelse,
            seen_assertions=else_seen,
            unittest_receiver_name=unittest_receiver_name,
        ):
            return True
        if _is_static_falsy(statement.test):
            _overwrite_seen_assertions(seen_assertions, else_seen)
        return False

    if isinstance(statement, ast.Try):
        branch_end_states: list[set[_AssertionKey]] = []

        body_seen = set(seen_assertions)
        if _block_has_duplicate_assertion(
            statement.body,
            seen_assertions=body_seen,
            unittest_receiver_name=unittest_receiver_name,
        ):
            return True
        orelse_seen = set(body_seen)
        if _block_has_duplicate_assertion(
            statement.orelse,
            seen_assertions=orelse_seen,
            unittest_receiver_name=unittest_receiver_name,
        ):
            return True
        branch_end_states.append(orelse_seen)

        for handler in statement.handlers:
            handler_seen = set(seen_assertions)
            if handler.type is not None and _record_expression_assertions(
                handler.type,
                seen_assertions=handler_seen,
                unittest_receiver_name=unittest_receiver_name,
            ):
                return True
            if _block_has_duplicate_assertion(
                handler.body,
                seen_assertions=handler_seen,
                unittest_receiver_name=unittest_receiver_name,
            ):
                return True
            branch_end_states.append(handler_seen)

        final_states = branch_end_states
        if statement.finalbody:
            final_states = []
            for branch_seen in branch_end_states:
                final_seen = set(branch_seen)
                if _block_has_duplicate_assertion(
                    statement.finalbody,
                    seen_assertions=final_seen,
                    unittest_receiver_name=unittest_receiver_name,
                ):
                    return True
                final_states.append(final_seen)

        _overwrite_seen_assertions(seen_assertions, _intersect_seen_assertions(final_states))
        return False

    if isinstance(statement, ast.Match):
        case_end_states: list[set[_AssertionKey]] = []
        for case in statement.cases:
            case_seen = set(seen_assertions)
            if case.guard is not None and _record_expression_assertions(
                case.guard,
                seen_assertions=case_seen,
                unittest_receiver_name=unittest_receiver_name,
            ):
                return True
            if _block_has_duplicate_assertion(
                case.body,
                seen_assertions=case_seen,
                unittest_receiver_name=unittest_receiver_name,
            ):
                return True
            case_end_states.append(case_seen)
        if case_end_states:
            _overwrite_seen_assertions(seen_assertions, _intersect_seen_assertions(case_end_states))
        return False

    return False


def _record_statement_header_assertions(
    statement: ast.stmt,
    *,
    seen_assertions: set[_AssertionKey],
    unittest_receiver_name: str | None,
) -> bool:
    for expression in _iter_statement_header_expressions(statement):
        if _record_expression_assertions(
            expression,
            seen_assertions=seen_assertions,
            unittest_receiver_name=unittest_receiver_name,
        ):
            return True
    return False


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


def _record_expression_assertions(
    expression: ast.AST,
    *,
    seen_assertions: set[_AssertionKey],
    unittest_receiver_name: str | None,
) -> bool:
    stack: list[ast.AST] = [expression]

    while stack:
        node = stack.pop()
        if isinstance(node, ast.Call):
            key = _normalize_unittest_assertion_call(node, unittest_receiver_name)
            if key is not None and _record_assertion_key(key, seen_assertions=seen_assertions):
                return True
        if isinstance(node, ast.Lambda):
            continue
        children = list(ast.iter_child_nodes(node))
        for child in reversed(children):
            stack.append(child)

    return False


def _record_assertion_key(
    key: _AssertionKey,
    *,
    seen_assertions: set[_AssertionKey],
) -> bool:
    if key in seen_assertions:
        return True
    seen_assertions.add(key)
    return False


def _overwrite_seen_assertions(
    target: set[_AssertionKey],
    source: set[_AssertionKey],
) -> None:
    target.clear()
    target.update(source)


def _intersect_seen_assertions(states: list[set[_AssertionKey]]) -> set[_AssertionKey]:
    if not states:
        return set()
    intersection = set(states[0])
    for state in states[1:]:
        intersection.intersection_update(state)
    return intersection


def _normalize_bare_assert(statement: ast.Assert) -> _AssertionKey:
    return ("assert", _normalize_ast(statement.test))


def _normalize_unittest_assertion_call(
    node: ast.Call,
    receiver_name: str | None,
) -> _AssertionKey | None:
    if receiver_name is None:
        return None
    if not isinstance(node.func, ast.Attribute):
        return None
    if not isinstance(node.func.value, ast.Name) or node.func.value.id != receiver_name:
        return None
    if not (node.func.attr.startswith("assert") or node.func.attr == "fail"):
        return None

    keywords = [
        (
            keyword.arg if keyword.arg is not None else "**",
            _normalize_ast(keyword.value),
        )
        for keyword in node.keywords
        if keyword.arg != "msg"
    ]
    keywords.sort(key=lambda item: (item[0], repr(item[1])))
    return (
        "unittest",
        (
            node.func.attr,
            tuple(_normalize_ast(argument) for argument in node.args),
            tuple(keywords),
        ),
    )


def _normalize_ast(node: _NormalizedValue) -> _NormalizedValue:
    if isinstance(node, ast.AST):
        fields: list[tuple[str, _NormalizedValue]] = []
        for field_name, value in ast.iter_fields(node):
            if field_name in _IGNORED_NORMALIZED_FIELDS:
                continue
            fields.append((field_name, _normalize_ast(value)))
        return (node.__class__.__name__, tuple(fields))
    if isinstance(node, list):
        return tuple(_normalize_ast(item) for item in node)
    if isinstance(node, tuple):
        return tuple(_normalize_ast(item) for item in node)
    return node


def _is_static_truthy(expression: ast.AST) -> bool:
    return isinstance(expression, ast.Constant) and bool(expression.value) is True


def _is_static_falsy(expression: ast.AST) -> bool:
    return isinstance(expression, ast.Constant) and bool(expression.value) is False
