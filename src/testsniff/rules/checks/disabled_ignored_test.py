from __future__ import annotations

import ast
from collections.abc import Sequence
from dataclasses import dataclass

from testsniff.config.types import Confidence, Severity
from testsniff.docs.rule_metadata import DISABLED_IGNORED_TEST
from testsniff.parser.ast_index import TestTarget
from testsniff.parser.module_context import ModuleContext
from testsniff.reporting.finding import Finding

_PYTEST_DISABLED_MARKERS = frozenset({"skip", "skipif"})
_UNITTEST_DISABLED_DECORATORS = frozenset({"skip", "skipIf", "skipUnless"})


@dataclass(slots=True, frozen=True)
class _DecoratorAliasState:
    pytest_module_aliases: frozenset[str]
    unittest_module_aliases: frozenset[str]
    unittest_case_aliases: frozenset[str]
    unittest_skip_names: frozenset[str]


@dataclass(slots=True)
class _MutableDecoratorAliasState:
    pytest_module_aliases: set[str]
    unittest_module_aliases: set[str]
    unittest_case_aliases: set[str]
    unittest_skip_names: set[str]


_EMPTY_ALIAS_STATE = _DecoratorAliasState(
    pytest_module_aliases=frozenset(),
    unittest_module_aliases=frozenset(),
    unittest_case_aliases=frozenset(),
    unittest_skip_names=frozenset(),
)


@dataclass(slots=True)
class DisabledIgnoredTestRule:
    rule_id: str = DISABLED_IGNORED_TEST.rule_id
    default_severity: Severity = DISABLED_IGNORED_TEST.default_severity
    default_confidence: Confidence = DISABLED_IGNORED_TEST.default_confidence

    def analyze(self, module: ModuleContext) -> list[Finding]:
        if not isinstance(module.tree, ast.Module):
            return []

        module_aliases = _build_alias_snapshots(module.tree.body)
        class_nodes = {
            statement.name: statement
            for statement in module.tree.body
            if isinstance(statement, ast.ClassDef)
        }
        class_aliases = {
            class_name: _build_alias_snapshots(
                class_node.body,
                initial_state=module_aliases.get(id(class_node), _EMPTY_ALIAS_STATE),
            )
            for class_name, class_node in class_nodes.items()
        }

        findings: list[Finding] = []
        for target in module.index.test_targets:
            if not _is_disabled_target(
                target,
                module_aliases=module_aliases,
                class_nodes=class_nodes,
                class_aliases=class_aliases,
            ):
                continue

            function = target.node
            findings.append(
                Finding(
                    rule_id=self.rule_id,
                    headline=DISABLED_IGNORED_TEST.headline,
                    severity=self.default_severity,
                    confidence=self.default_confidence,
                    path=str(module.path),
                    line=function.lineno,
                    column=function.col_offset + 1,
                    why=DISABLED_IGNORED_TEST.why,
                    fix=DISABLED_IGNORED_TEST.fix,
                    example=DISABLED_IGNORED_TEST.example,
                    references=DISABLED_IGNORED_TEST.references,
                )
            )

        return findings


def _is_disabled_target(
    target: TestTarget,
    *,
    module_aliases: dict[int, _DecoratorAliasState],
    class_nodes: dict[str, ast.ClassDef],
    class_aliases: dict[str, dict[int, _DecoratorAliasState]],
) -> bool:
    if target.class_name is None:
        alias_state = module_aliases.get(id(target.node), _EMPTY_ALIAS_STATE)
        return _has_disabled_decorator(target.node.decorator_list, alias_state)

    class_node = class_nodes.get(target.class_name)
    if class_node is None:
        return False

    class_alias_state = module_aliases.get(id(class_node), _EMPTY_ALIAS_STATE)
    if _has_disabled_decorator(class_node.decorator_list, class_alias_state):
        return True

    method_alias_state = class_aliases.get(target.class_name, {}).get(
        id(target.node), class_alias_state
    )
    return _has_disabled_decorator(target.node.decorator_list, method_alias_state)


def _has_disabled_decorator(
    decorators: Sequence[ast.expr],
    alias_state: _DecoratorAliasState,
) -> bool:
    for decorator in decorators:
        candidate = decorator.func if isinstance(decorator, ast.Call) else decorator
        dotted_name = _as_dotted_name(candidate)
        if dotted_name is None:
            continue
        if _is_pytest_disabled_decorator(dotted_name, alias_state):
            return True
        if _is_unittest_disabled_decorator(dotted_name, alias_state):
            return True
    return False


def _is_pytest_disabled_decorator(
    dotted_name: str,
    alias_state: _DecoratorAliasState,
) -> bool:
    for alias in alias_state.pytest_module_aliases:
        for marker_name in _PYTEST_DISABLED_MARKERS:
            if dotted_name == f"{alias}.mark.{marker_name}":
                return True
    return False


def _is_unittest_disabled_decorator(
    dotted_name: str,
    alias_state: _DecoratorAliasState,
) -> bool:
    if dotted_name in alias_state.unittest_skip_names:
        return True

    for alias in alias_state.unittest_module_aliases:
        for decorator_name in _UNITTEST_DISABLED_DECORATORS:
            if dotted_name == f"{alias}.{decorator_name}":
                return True
            if dotted_name == f"{alias}.case.{decorator_name}":
                return True

    for alias in alias_state.unittest_case_aliases:
        for decorator_name in _UNITTEST_DISABLED_DECORATORS:
            if dotted_name == f"{alias}.{decorator_name}":
                return True

    return False


def _build_alias_snapshots(
    statements: Sequence[ast.stmt],
    *,
    initial_state: _DecoratorAliasState | None = None,
) -> dict[int, _DecoratorAliasState]:
    state = _mutable_alias_state(initial_state or _EMPTY_ALIAS_STATE)
    snapshots: dict[int, _DecoratorAliasState] = {}

    for statement in statements:
        snapshots[id(statement)] = _freeze_alias_state(state)
        if isinstance(statement, ast.Import):
            _apply_import_alias_updates(statement, state)
            continue
        if isinstance(statement, ast.ImportFrom):
            _apply_import_from_alias_updates(statement, state)
            continue
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            _discard_aliases({statement.name}, state)
            continue

        rebound_names = _collect_rebound_names(statement)
        if rebound_names:
            _discard_aliases(rebound_names, state)

    return snapshots


def _mutable_alias_state(alias_state: _DecoratorAliasState) -> _MutableDecoratorAliasState:
    return _MutableDecoratorAliasState(
        pytest_module_aliases=set(alias_state.pytest_module_aliases),
        unittest_module_aliases=set(alias_state.unittest_module_aliases),
        unittest_case_aliases=set(alias_state.unittest_case_aliases),
        unittest_skip_names=set(alias_state.unittest_skip_names),
    )


def _freeze_alias_state(alias_state: _MutableDecoratorAliasState) -> _DecoratorAliasState:
    return _DecoratorAliasState(
        pytest_module_aliases=frozenset(alias_state.pytest_module_aliases),
        unittest_module_aliases=frozenset(alias_state.unittest_module_aliases),
        unittest_case_aliases=frozenset(alias_state.unittest_case_aliases),
        unittest_skip_names=frozenset(alias_state.unittest_skip_names),
    )


def _apply_import_alias_updates(
    statement: ast.Import,
    alias_state: _MutableDecoratorAliasState,
) -> None:
    bound_names = {alias.asname or alias.name.split(".")[0] for alias in statement.names}
    _discard_aliases(bound_names, alias_state)

    for alias in statement.names:
        bound_name = alias.asname or alias.name.split(".")[0]
        if alias.name == "pytest":
            alias_state.pytest_module_aliases.add(bound_name)
            continue
        if alias.name == "unittest":
            alias_state.unittest_module_aliases.add(bound_name)
            continue
        if alias.name == "unittest.case":
            if alias.asname is None:
                alias_state.unittest_module_aliases.add(bound_name)
            else:
                alias_state.unittest_case_aliases.add(alias.asname)


def _apply_import_from_alias_updates(
    statement: ast.ImportFrom,
    alias_state: _MutableDecoratorAliasState,
) -> None:
    bound_names = {alias.asname or alias.name for alias in statement.names}
    _discard_aliases(bound_names, alias_state)

    if statement.module == "unittest":
        for alias in statement.names:
            bound_name = alias.asname or alias.name
            if alias.name in _UNITTEST_DISABLED_DECORATORS:
                alias_state.unittest_skip_names.add(bound_name)
            elif alias.name == "case":
                alias_state.unittest_case_aliases.add(bound_name)
        return

    if statement.module == "unittest.case":
        for alias in statement.names:
            if alias.name in _UNITTEST_DISABLED_DECORATORS:
                alias_state.unittest_skip_names.add(alias.asname or alias.name)


def _discard_aliases(
    rebound_names: set[str],
    alias_state: _MutableDecoratorAliasState,
) -> None:
    alias_state.pytest_module_aliases.difference_update(rebound_names)
    alias_state.unittest_module_aliases.difference_update(rebound_names)
    alias_state.unittest_case_aliases.difference_update(rebound_names)
    alias_state.unittest_skip_names.difference_update(rebound_names)


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


def _as_dotted_name(node: ast.expr) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _as_dotted_name(node.value)
        if parent is None:
            return None
        return f"{parent}.{node.attr}"
    return None
