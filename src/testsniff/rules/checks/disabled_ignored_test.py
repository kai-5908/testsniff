from __future__ import annotations

import ast
from dataclasses import dataclass

from testsniff.config.types import Confidence, Severity
from testsniff.docs.rule_metadata import DISABLED_IGNORED_TEST
from testsniff.parser.ast_index import TestTarget
from testsniff.parser.module_context import ModuleContext
from testsniff.reporting.finding import Finding

_PYTEST_DISABLED_MARKERS = frozenset({"skip", "skipif"})
_UNITTEST_DISABLED_DECORATORS = frozenset({"skip", "skipIf", "skipUnless"})


@dataclass(slots=True)
class _DecoratorAliasState:
    pytest_module_aliases: set[str]
    unittest_module_aliases: set[str]
    unittest_case_aliases: set[str]
    unittest_skip_names: set[str]


@dataclass(slots=True)
class DisabledIgnoredTestRule:
    rule_id: str = DISABLED_IGNORED_TEST.rule_id
    default_severity: Severity = DISABLED_IGNORED_TEST.default_severity
    default_confidence: Confidence = DISABLED_IGNORED_TEST.default_confidence

    def analyze(self, module: ModuleContext) -> list[Finding]:
        if not isinstance(module.tree, ast.Module):
            return []

        targets_by_node_id = {id(target.node): target for target in module.index.test_targets}
        targets_by_class_node_id: dict[int, list[TestTarget]] = {}
        for target in module.index.test_targets:
            if target.class_node is None:
                continue
            targets_by_class_node_id.setdefault(id(target.class_node), []).append(target)

        findings: list[Finding] = []
        reported_target_ids: set[int] = set()
        _collect_findings_from_block(
            module.tree.body,
            module_path=str(module.path),
            alias_state=_new_alias_state(),
            targets_by_node_id=targets_by_node_id,
            targets_by_class_node_id=targets_by_class_node_id,
            findings=findings,
            reported_target_ids=reported_target_ids,
        )
        return findings


def _collect_findings_from_block(
    statements: list[ast.stmt],
    *,
    module_path: str,
    alias_state: _DecoratorAliasState,
    targets_by_node_id: dict[int, TestTarget],
    targets_by_class_node_id: dict[int, list[TestTarget]],
    findings: list[Finding],
    reported_target_ids: set[int],
) -> None:
    for statement in statements:
        if isinstance(statement, ast.Import):
            _apply_import_alias_updates(statement, alias_state)
            continue

        if isinstance(statement, ast.ImportFrom):
            _apply_import_from_alias_updates(statement, alias_state)
            continue

        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
            _report_target_if_disabled(
                targets_by_node_id.get(id(statement)),
                statement.decorator_list,
                module_path,
                alias_state,
                findings,
                reported_target_ids,
            )
            _discard_aliases({statement.name}, alias_state)
            continue

        if isinstance(statement, ast.ClassDef):
            _report_class_targets_if_disabled(
                statement,
                module_path,
                alias_state,
                targets_by_class_node_id,
                findings,
                reported_target_ids,
            )
            _collect_findings_from_block(
                statement.body,
                module_path=module_path,
                alias_state=_copy_alias_state(alias_state),
                targets_by_node_id=targets_by_node_id,
                targets_by_class_node_id=targets_by_class_node_id,
                findings=findings,
                reported_target_ids=reported_target_ids,
            )
            _discard_aliases({statement.name}, alias_state)
            continue

        if isinstance(statement, ast.With | ast.AsyncWith):
            body_aliases = _copy_alias_state(alias_state)
            _discard_aliases(_collect_with_optional_var_names(statement), body_aliases)
            _collect_findings_from_block(
                statement.body,
                module_path=module_path,
                alias_state=body_aliases,
                targets_by_node_id=targets_by_node_id,
                targets_by_class_node_id=targets_by_class_node_id,
                findings=findings,
                reported_target_ids=reported_target_ids,
            )
            _overwrite_alias_state(alias_state, body_aliases)
            continue

        if isinstance(statement, ast.For | ast.AsyncFor):
            body_aliases = _copy_alias_state(alias_state)
            _discard_aliases(_collect_target_names(statement.target), body_aliases)
            _collect_findings_from_block(
                statement.body,
                module_path=module_path,
                alias_state=body_aliases,
                targets_by_node_id=targets_by_node_id,
                targets_by_class_node_id=targets_by_class_node_id,
                findings=findings,
                reported_target_ids=reported_target_ids,
            )
            loop_aliases = _copy_alias_state(body_aliases)
            _collect_findings_from_block(
                statement.orelse,
                module_path=module_path,
                alias_state=loop_aliases,
                targets_by_node_id=targets_by_node_id,
                targets_by_class_node_id=targets_by_class_node_id,
                findings=findings,
                reported_target_ids=reported_target_ids,
            )
            _overwrite_alias_state(
                alias_state,
                _merge_alias_state_intersection(
                    _merge_alias_state_intersection(_copy_alias_state(alias_state), body_aliases),
                    loop_aliases,
                ),
            )
            continue

        if isinstance(statement, ast.Try):
            success_aliases = _copy_alias_state(alias_state)
            _collect_findings_from_block(
                statement.body,
                module_path=module_path,
                alias_state=success_aliases,
                targets_by_node_id=targets_by_node_id,
                targets_by_class_node_id=targets_by_class_node_id,
                findings=findings,
                reported_target_ids=reported_target_ids,
            )
            _collect_findings_from_block(
                statement.orelse,
                module_path=module_path,
                alias_state=success_aliases,
                targets_by_node_id=targets_by_node_id,
                targets_by_class_node_id=targets_by_class_node_id,
                findings=findings,
                reported_target_ids=reported_target_ids,
            )

            merged_aliases = success_aliases
            for handler in statement.handlers:
                handler_aliases = _copy_alias_state(alias_state)
                if handler.name is not None:
                    _discard_aliases({handler.name}, handler_aliases)
                _collect_findings_from_block(
                    handler.body,
                    module_path=module_path,
                    alias_state=handler_aliases,
                    targets_by_node_id=targets_by_node_id,
                    targets_by_class_node_id=targets_by_class_node_id,
                    findings=findings,
                    reported_target_ids=reported_target_ids,
                )
                merged_aliases = _merge_alias_state_intersection(
                    merged_aliases,
                    handler_aliases,
                )

            _collect_findings_from_block(
                statement.finalbody,
                module_path=module_path,
                alias_state=merged_aliases,
                targets_by_node_id=targets_by_node_id,
                targets_by_class_node_id=targets_by_class_node_id,
                findings=findings,
                reported_target_ids=reported_target_ids,
            )
            _overwrite_alias_state(alias_state, merged_aliases)
            continue

        if isinstance(statement, ast.If):
            body_aliases = _copy_alias_state(alias_state)
            _collect_findings_from_block(
                statement.body,
                module_path=module_path,
                alias_state=body_aliases,
                targets_by_node_id=targets_by_node_id,
                targets_by_class_node_id=targets_by_class_node_id,
                findings=findings,
                reported_target_ids=reported_target_ids,
            )
            else_aliases = _copy_alias_state(alias_state)
            _collect_findings_from_block(
                statement.orelse,
                module_path=module_path,
                alias_state=else_aliases,
                targets_by_node_id=targets_by_node_id,
                targets_by_class_node_id=targets_by_class_node_id,
                findings=findings,
                reported_target_ids=reported_target_ids,
            )
            if _is_static_truthy(statement.test):
                _overwrite_alias_state(alias_state, body_aliases)
            elif _is_static_falsy(statement.test):
                _overwrite_alias_state(alias_state, else_aliases)
            else:
                _overwrite_alias_state(
                    alias_state,
                    _merge_alias_state_intersection(body_aliases, else_aliases),
                )
            continue

        if isinstance(statement, ast.While):
            body_aliases = _copy_alias_state(alias_state)
            _collect_findings_from_block(
                statement.body,
                module_path=module_path,
                alias_state=body_aliases,
                targets_by_node_id=targets_by_node_id,
                targets_by_class_node_id=targets_by_class_node_id,
                findings=findings,
                reported_target_ids=reported_target_ids,
            )
            else_aliases = _copy_alias_state(alias_state)
            _collect_findings_from_block(
                statement.orelse,
                module_path=module_path,
                alias_state=else_aliases,
                targets_by_node_id=targets_by_node_id,
                targets_by_class_node_id=targets_by_class_node_id,
                findings=findings,
                reported_target_ids=reported_target_ids,
            )
            if _is_static_falsy(statement.test):
                _overwrite_alias_state(alias_state, else_aliases)
            else:
                _overwrite_alias_state(
                    alias_state,
                    _merge_alias_state_intersection(
                        _merge_alias_state_intersection(
                            _copy_alias_state(alias_state),
                            body_aliases,
                        ),
                        else_aliases,
                    ),
                )
            continue

        if isinstance(statement, ast.Match):
            merged_aliases = _copy_alias_state(alias_state)
            for case in statement.cases:
                case_aliases = _copy_alias_state(alias_state)
                _discard_aliases(_collect_pattern_capture_names(case.pattern), case_aliases)
                _collect_findings_from_block(
                    case.body,
                    module_path=module_path,
                    alias_state=case_aliases,
                    targets_by_node_id=targets_by_node_id,
                    targets_by_class_node_id=targets_by_class_node_id,
                    findings=findings,
                    reported_target_ids=reported_target_ids,
                )
                merged_aliases = _merge_alias_state_intersection(merged_aliases, case_aliases)
            _overwrite_alias_state(alias_state, merged_aliases)
            continue

        rebound_names = _collect_rebound_names(statement)
        if rebound_names:
            _discard_aliases(rebound_names, alias_state)


def _report_target_if_disabled(
    target: TestTarget | None,
    decorators: list[ast.expr],
    module_path: str,
    alias_state: _DecoratorAliasState,
    findings: list[Finding],
    reported_target_ids: set[int],
) -> None:
    if target is None or id(target.node) in reported_target_ids:
        return
    if not _has_disabled_decorator(decorators, alias_state):
        return
    findings.append(_finding_for_target(target, module_path))
    reported_target_ids.add(id(target.node))


def _report_class_targets_if_disabled(
    class_node: ast.ClassDef,
    module_path: str,
    alias_state: _DecoratorAliasState,
    targets_by_class_node_id: dict[int, list[TestTarget]],
    findings: list[Finding],
    reported_target_ids: set[int],
) -> None:
    if not _has_disabled_decorator(class_node.decorator_list, alias_state):
        return
    for target in targets_by_class_node_id.get(id(class_node), ()):
        if id(target.node) in reported_target_ids:
            continue
        findings.append(_finding_for_target(target, module_path))
        reported_target_ids.add(id(target.node))


def _finding_for_target(target: TestTarget, module_path: str) -> Finding:
    function = target.node
    return Finding(
        rule_id=DISABLED_IGNORED_TEST.rule_id,
        headline=DISABLED_IGNORED_TEST.headline,
        severity=DISABLED_IGNORED_TEST.default_severity,
        confidence=DISABLED_IGNORED_TEST.default_confidence,
        path=module_path,
        line=function.lineno,
        column=function.col_offset + 1,
        why=DISABLED_IGNORED_TEST.why,
        fix=DISABLED_IGNORED_TEST.fix,
        example=DISABLED_IGNORED_TEST.example,
        references=DISABLED_IGNORED_TEST.references,
    )


def _has_disabled_decorator(
    decorators: list[ast.expr],
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
    return any(
        dotted_name == f"{alias}.mark.{marker_name}"
        for alias in alias_state.pytest_module_aliases
        for marker_name in _PYTEST_DISABLED_MARKERS
    )


def _is_unittest_disabled_decorator(
    dotted_name: str,
    alias_state: _DecoratorAliasState,
) -> bool:
    if dotted_name in alias_state.unittest_skip_names:
        return True
    if any(
        dotted_name in {f"{alias}.{decorator}", f"{alias}.case.{decorator}"}
        for alias in alias_state.unittest_module_aliases
        for decorator in _UNITTEST_DISABLED_DECORATORS
    ):
        return True
    return any(
        dotted_name == f"{alias}.{decorator}"
        for alias in alias_state.unittest_case_aliases
        for decorator in _UNITTEST_DISABLED_DECORATORS
    )


def _new_alias_state() -> _DecoratorAliasState:
    return _DecoratorAliasState(
        pytest_module_aliases=set(),
        unittest_module_aliases=set(),
        unittest_case_aliases=set(),
        unittest_skip_names=set(),
    )


def _copy_alias_state(alias_state: _DecoratorAliasState) -> _DecoratorAliasState:
    return _DecoratorAliasState(
        pytest_module_aliases=set(alias_state.pytest_module_aliases),
        unittest_module_aliases=set(alias_state.unittest_module_aliases),
        unittest_case_aliases=set(alias_state.unittest_case_aliases),
        unittest_skip_names=set(alias_state.unittest_skip_names),
    )


def _overwrite_alias_state(
    target: _DecoratorAliasState,
    source: _DecoratorAliasState,
) -> None:
    target.pytest_module_aliases.clear()
    target.pytest_module_aliases.update(source.pytest_module_aliases)
    target.unittest_module_aliases.clear()
    target.unittest_module_aliases.update(source.unittest_module_aliases)
    target.unittest_case_aliases.clear()
    target.unittest_case_aliases.update(source.unittest_case_aliases)
    target.unittest_skip_names.clear()
    target.unittest_skip_names.update(source.unittest_skip_names)


def _merge_alias_state_intersection(
    left: _DecoratorAliasState,
    right: _DecoratorAliasState,
) -> _DecoratorAliasState:
    return _DecoratorAliasState(
        pytest_module_aliases=left.pytest_module_aliases & right.pytest_module_aliases,
        unittest_module_aliases=left.unittest_module_aliases & right.unittest_module_aliases,
        unittest_case_aliases=left.unittest_case_aliases & right.unittest_case_aliases,
        unittest_skip_names=left.unittest_skip_names & right.unittest_skip_names,
    )


def _apply_import_alias_updates(
    statement: ast.Import,
    alias_state: _DecoratorAliasState,
) -> None:
    _discard_aliases(
        {alias.asname or alias.name.split(".")[0] for alias in statement.names},
        alias_state,
    )
    for alias in statement.names:
        bound_name = alias.asname or alias.name.split(".")[0]
        if alias.name == "pytest":
            alias_state.pytest_module_aliases.add(bound_name)
        elif alias.name == "unittest":
            alias_state.unittest_module_aliases.add(bound_name)
        elif alias.name == "unittest.case":
            if alias.asname is None:
                alias_state.unittest_module_aliases.add(bound_name)
            else:
                alias_state.unittest_case_aliases.add(alias.asname)


def _apply_import_from_alias_updates(
    statement: ast.ImportFrom,
    alias_state: _DecoratorAliasState,
) -> None:
    _discard_aliases({alias.asname or alias.name for alias in statement.names}, alias_state)

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
    alias_state: _DecoratorAliasState,
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
    if isinstance(statement, ast.ExceptHandler) and statement.name is not None:
        return {statement.name}
    return set()


def _collect_with_optional_var_names(statement: ast.With | ast.AsyncWith) -> set[str]:
    names: set[str] = set()
    for item in statement.items:
        if item.optional_vars is not None:
            names.update(_collect_target_names(item.optional_vars))
    return names


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


def _collect_pattern_capture_names(pattern: ast.pattern) -> set[str]:
    if isinstance(pattern, ast.MatchAs):
        names = {pattern.name} if pattern.name is not None else set()
        if pattern.pattern is not None:
            names.update(_collect_pattern_capture_names(pattern.pattern))
        return names
    if isinstance(pattern, ast.MatchStar):
        return {pattern.name} if pattern.name is not None else set()
    if isinstance(pattern, ast.MatchMapping):
        names: set[str] = set()
        for child in pattern.patterns:
            names.update(_collect_pattern_capture_names(child))
        if pattern.rest is not None:
            names.add(pattern.rest)
        return names
    if isinstance(pattern, ast.MatchSequence):
        names: set[str] = set()
        for child in pattern.patterns:
            names.update(_collect_pattern_capture_names(child))
        return names
    if isinstance(pattern, ast.MatchClass):
        names: set[str] = set()
        for child in pattern.patterns:
            names.update(_collect_pattern_capture_names(child))
        for child in pattern.kwd_patterns:
            names.update(_collect_pattern_capture_names(child))
        return names
    if isinstance(pattern, ast.MatchOr):
        names: set[str] = set()
        for child in pattern.patterns:
            names.update(_collect_pattern_capture_names(child))
        return names
    return set()


def _is_static_truthy(expression: ast.AST) -> bool:
    return isinstance(expression, ast.Constant) and bool(expression.value) is True


def _is_static_falsy(expression: ast.AST) -> bool:
    return isinstance(expression, ast.Constant) and bool(expression.value) is False


def _as_dotted_name(node: ast.expr) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _as_dotted_name(node.value)
        if parent is None:
            return None
        return f"{parent}.{node.attr}"
    return None
