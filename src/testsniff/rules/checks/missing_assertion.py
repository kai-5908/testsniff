from __future__ import annotations

import ast
from dataclasses import dataclass

from testsniff.config.types import Confidence, Severity
from testsniff.docs.rule_metadata import MISSING_ASSERTION
from testsniff.parser.ast_index import FunctionNode, TestTarget
from testsniff.parser.module_context import ModuleContext
from testsniff.reporting.finding import Finding
from testsniff.rules.checks._function_body import is_effectively_empty, iter_executable_body

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
            if is_effectively_empty(target.node):
                continue
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
            _discard_pytest_aliases(
                {alias.asname or alias.name.split(".")[0] for alias in statement.names},
                module_aliases,
                helper_names,
            )
            for alias in statement.names:
                if alias.name == "pytest":
                    module_aliases.add(alias.asname or alias.name)
            continue

        if isinstance(statement, ast.ImportFrom):
            _discard_pytest_aliases(
                {alias.asname or alias.name for alias in statement.names},
                module_aliases,
                helper_names,
            )
            if statement.module == "pytest":
                for alias in statement.names:
                    if alias.name in _PYTEST_HELPERS:
                        helper_names.add(alias.asname or alias.name)
            continue

        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            _discard_pytest_aliases({statement.name}, module_aliases, helper_names)
            continue

        rebound_names = _collect_rebound_names(statement)
        if rebound_names:
            _discard_pytest_aliases(rebound_names, module_aliases, helper_names)

    return _PytestAliasSet(
        module_aliases=frozenset(module_aliases),
        helper_names=frozenset(helper_names),
    )


def _has_recognized_assertion(target: TestTarget, pytest_aliases: _PytestAliasSet) -> bool:
    receiver_name = _get_instance_receiver_name(target)
    active_aliases = _TargetPytestAliases(
        module_aliases=set(pytest_aliases.module_aliases),
        helper_names=set(pytest_aliases.helper_names),
    )
    _discard_pytest_aliases(
        _collect_parameter_names(target.node),
        active_aliases.module_aliases,
        active_aliases.helper_names,
    )

    for statement in iter_executable_body(target.node):
        if _statement_has_recognized_assertion(
            statement,
            unittest_receiver_name=receiver_name if target.style == "unittest" else None,
            pytest_aliases=active_aliases,
        ):
            return True
        _apply_statement_alias_updates(statement, active_aliases)

    return False


@dataclass(slots=True)
class _TargetPytestAliases:
    module_aliases: set[str]
    helper_names: set[str]


def _get_instance_receiver_name(target: TestTarget) -> str | None:
    arguments = target.node.args.posonlyargs + target.node.args.args
    if not arguments:
        return None
    return arguments[0].arg if target.class_name is not None else None


def _collect_parameter_names(function: FunctionNode) -> set[str]:
    names = {argument.arg for argument in function.args.posonlyargs}
    names.update(argument.arg for argument in function.args.args)
    names.update(argument.arg for argument in function.args.kwonlyargs)
    if function.args.vararg is not None:
        names.add(function.args.vararg.arg)
    if function.args.kwarg is not None:
        names.add(function.args.kwarg.arg)
    return names


def _apply_statement_alias_updates(
    statement: ast.stmt,
    pytest_aliases: _TargetPytestAliases,
) -> None:
    if isinstance(statement, ast.Import):
        _discard_pytest_aliases(
            {alias.asname or alias.name.split(".")[0] for alias in statement.names},
            pytest_aliases.module_aliases,
            pytest_aliases.helper_names,
        )
        for alias in statement.names:
            if alias.name == "pytest":
                pytest_aliases.module_aliases.add(alias.asname or alias.name)
        return

    if isinstance(statement, ast.ImportFrom):
        _discard_pytest_aliases(
            {alias.asname or alias.name for alias in statement.names},
            pytest_aliases.module_aliases,
            pytest_aliases.helper_names,
        )
        if statement.module == "pytest":
            for alias in statement.names:
                if alias.name in _PYTEST_HELPERS:
                    pytest_aliases.helper_names.add(alias.asname or alias.name)
        return

    if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        _discard_pytest_aliases(
            {statement.name},
            pytest_aliases.module_aliases,
            pytest_aliases.helper_names,
        )
        return

    rebound_names = _collect_rebound_names(statement)
    if rebound_names:
        _discard_pytest_aliases(
            rebound_names,
            pytest_aliases.module_aliases,
            pytest_aliases.helper_names,
        )


def _statement_has_recognized_assertion(
    statement: ast.stmt,
    *,
    unittest_receiver_name: str | None,
    pytest_aliases: _TargetPytestAliases,
) -> bool:
    for node in _iter_statement_nodes(statement):
        if isinstance(node, ast.Assert):
            return True
        if isinstance(node, ast.Call) and (
            _is_unittest_assertion_call(node, unittest_receiver_name)
            or _is_pytest_assertion_call(node, pytest_aliases)
        ):
            return True
    return False


def _iter_statement_nodes(statement: ast.stmt) -> list[ast.AST]:
    nodes: list[ast.AST] = []
    stack: list[tuple[ast.AST, bool]] = [(statement, True)]

    while stack:
        node, descend = stack.pop()
        nodes.append(node)
        if not descend:
            continue
        if node is not statement and isinstance(
            node,
            (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda),
        ):
            continue
        children = list(ast.iter_child_nodes(node))
        for child in reversed(children):
            stack.append((child, True))

    return nodes


def _discard_pytest_aliases(
    rebound_names: set[str],
    module_aliases: set[str],
    helper_names: set[str],
) -> None:
    module_aliases.difference_update(rebound_names)
    helper_names.difference_update(rebound_names)


def _collect_rebound_names(statement: ast.stmt) -> set[str]:
    if isinstance(statement, ast.Assign):
        names: set[str] = set()
        for target in statement.targets:
            names.update(_collect_target_names(target))
        return names
    if isinstance(statement, (ast.AnnAssign, ast.AugAssign)):
        return _collect_target_names(statement.target)
    if isinstance(statement, (ast.For, ast.AsyncFor)):
        return _collect_target_names(statement.target)
    if isinstance(statement, (ast.With, ast.AsyncWith)):
        names: set[str] = set()
        for item in statement.items:
            if item.optional_vars is not None:
                names.update(_collect_target_names(item.optional_vars))
        return names
    if isinstance(statement, ast.ExceptHandler) and statement.name is not None:
        return {statement.name}
    return set()


def _collect_target_names(target: ast.expr) -> set[str]:
    if isinstance(target, ast.Name):
        return {target.id}
    if isinstance(target, (ast.Tuple, ast.List)):
        names: set[str] = set()
        for element in target.elts:
            names.update(_collect_target_names(element))
        return names
    if isinstance(target, ast.Starred):
        return _collect_target_names(target.value)
    return set()


def _is_unittest_assertion_call(node: ast.Call, receiver_name: str | None) -> bool:
    if receiver_name is None:
        return False
    if not isinstance(node.func, ast.Attribute):
        return False
    if not isinstance(node.func.value, ast.Name) or node.func.value.id != receiver_name:
        return False
    return node.func.attr.startswith("assert") or node.func.attr == "fail"


def _is_pytest_assertion_call(node: ast.Call, pytest_aliases: _TargetPytestAliases) -> bool:
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
