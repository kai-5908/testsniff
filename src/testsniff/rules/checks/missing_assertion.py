from __future__ import annotations

import ast
from dataclasses import dataclass

from testsniff.config.types import Confidence, Severity
from testsniff.docs.rule_metadata import MISSING_ASSERTION
from testsniff.parser.ast_index import FunctionNode, TestTarget
from testsniff.parser.module_context import ModuleContext
from testsniff.reporting.finding import Finding

_PYTEST_HELPERS = frozenset({"raises", "warns", "fail"})


@dataclass(slots=True, frozen=True)
class _PytestAliasSet:
    module_aliases: frozenset[str]
    helper_names: frozenset[str]


@dataclass(slots=True)
class MissingAssertionRule:
    rule_id: str = MISSING_ASSERTION.rule_id
    default_severity: Severity = MISSING_ASSERTION.default_severity
    default_confidence: Confidence = MISSING_ASSERTION.default_confidence

    def analyze(self, module: ModuleContext) -> list[Finding]:
        pytest_aliases = _collect_pytest_aliases(module.tree)
        findings: list[Finding] = []

        for target in module.index.test_targets:
            if _has_recognized_assertion(target, pytest_aliases):
                continue

            function = target.node
            findings.append(
                Finding(
                    rule_id=self.rule_id,
                    headline=MISSING_ASSERTION.headline,
                    severity=self.default_severity,
                    confidence=self.default_confidence,
                    path=str(module.path),
                    line=function.lineno,
                    column=function.col_offset + 1,
                    why=MISSING_ASSERTION.why,
                    fix=MISSING_ASSERTION.fix,
                    example=MISSING_ASSERTION.example,
                    references=MISSING_ASSERTION.references,
                )
            )

        return findings


def _collect_pytest_aliases(tree: ast.AST) -> _PytestAliasSet:
    if not isinstance(tree, ast.Module):
        return _PytestAliasSet(module_aliases=frozenset(), helper_names=frozenset())

    module_aliases: set[str] = set()
    helper_names: set[str] = set()

    for statement in tree.body:
        if isinstance(statement, ast.Import):
            for alias in statement.names:
                if alias.name == "pytest":
                    module_aliases.add(alias.asname or alias.name)
            continue

        if isinstance(statement, ast.ImportFrom) and statement.module == "pytest":
            for alias in statement.names:
                if alias.name in _PYTEST_HELPERS:
                    helper_names.add(alias.asname or alias.name)

    return _PytestAliasSet(
        module_aliases=frozenset(module_aliases),
        helper_names=frozenset(helper_names),
    )


def _has_recognized_assertion(target: TestTarget, pytest_aliases: _PytestAliasSet) -> bool:
    receiver_name = _get_instance_receiver_name(target)
    visitor = _AssertionSignalVisitor(
        unittest_receiver_name=receiver_name if target.style == "unittest" else None,
        pytest_aliases=pytest_aliases,
    )

    for statement in _iter_function_body(target.node):
        visitor.visit(statement)
        if visitor.found_assertion:
            return True

    return False


def _get_instance_receiver_name(target: TestTarget) -> str | None:
    arguments = target.node.args.posonlyargs + target.node.args.args
    if not arguments:
        return None
    return arguments[0].arg if target.class_name is not None else None


def _iter_function_body(function: FunctionNode) -> list[ast.stmt]:
    body = list(function.body)
    if body and _is_string_literal_expr(body[0]):
        return body[1:]
    return body


def _is_string_literal_expr(statement: ast.stmt) -> bool:
    if not isinstance(statement, ast.Expr):
        return False
    return isinstance(statement.value, ast.Constant) and isinstance(statement.value.value, str)


class _AssertionSignalVisitor(ast.NodeVisitor):
    def __init__(
        self,
        *,
        unittest_receiver_name: str | None,
        pytest_aliases: _PytestAliasSet,
    ) -> None:
        self.unittest_receiver_name = unittest_receiver_name
        self.pytest_aliases = pytest_aliases
        self.found_assertion = False

    def visit(self, node: ast.AST) -> None:
        if self.found_assertion:
            return
        super().visit(node)

    def visit_Assert(self, node: ast.Assert) -> None:
        self.found_assertion = True

    def visit_Call(self, node: ast.Call) -> None:
        if _is_unittest_assertion_call(node, self.unittest_receiver_name):
            self.found_assertion = True
            return
        if _is_pytest_assertion_call(node, self.pytest_aliases):
            self.found_assertion = True
            return
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        return

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        return

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        return

    def visit_Lambda(self, node: ast.Lambda) -> None:
        return


def _is_unittest_assertion_call(node: ast.Call, receiver_name: str | None) -> bool:
    if receiver_name is None:
        return False
    if not isinstance(node.func, ast.Attribute):
        return False
    if not isinstance(node.func.value, ast.Name) or node.func.value.id != receiver_name:
        return False
    return node.func.attr.startswith("assert") or node.func.attr == "fail"


def _is_pytest_assertion_call(node: ast.Call, pytest_aliases: _PytestAliasSet) -> bool:
    if isinstance(node.func, ast.Attribute):
        if not isinstance(node.func.value, ast.Name):
            return False
        return (
            node.func.value.id in pytest_aliases.module_aliases
            and node.func.attr in _PYTEST_HELPERS
        )

    if isinstance(node.func, ast.Name):
        return node.func.id in pytest_aliases.helper_names

    return False
