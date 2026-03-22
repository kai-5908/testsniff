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
    unittest_skip_names: dict[str, str]


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
            _discard_aliases(_collect_named_expr_names(statement.test), alias_state)
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
            _discard_aliases(_collect_named_expr_names(statement.test), alias_state)
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
            _discard_aliases(_collect_named_expr_names(statement.subject), alias_state)
            merged_aliases = _copy_alias_state(alias_state)
            for case in statement.cases:
                case_aliases = _copy_alias_state(alias_state)
                _discard_aliases(_collect_pattern_capture_names(case.pattern), case_aliases)
                if case.guard is not None:
                    _discard_aliases(_collect_named_expr_names(case.guard), case_aliases)
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
        if _decorator_disables_target(decorator, alias_state):
            return True
    return False


def _decorator_disables_target(
    decorator: ast.expr,
    alias_state: _DecoratorAliasState,
) -> bool:
    candidate = decorator.func if isinstance(decorator, ast.Call) else decorator
    dotted_name = _as_dotted_name(candidate)
    if dotted_name is None:
        return False

    kind = _resolve_decorator_kind(dotted_name, alias_state)
    if kind is None:
        return False
    if kind == "skip":
        return True
    if kind in {"pytest_skipif", "skipIf"}:
        return _decorator_condition_disables_target(decorator, disabled_when=True)
    if kind == "skipUnless":
        return _decorator_condition_disables_target(decorator, disabled_when=False)
    return False


def _resolve_decorator_kind(
    dotted_name: str,
    alias_state: _DecoratorAliasState,
) -> str | None:
    for alias in alias_state.pytest_module_aliases:
        if dotted_name == f"{alias}.mark.skip":
            return "skip"
        if dotted_name == f"{alias}.mark.skipif":
            return "pytest_skipif"

    direct_unittest = alias_state.unittest_skip_names.get(dotted_name)
    if direct_unittest is not None:
        return direct_unittest

    for alias in alias_state.unittest_module_aliases:
        for decorator_name in _UNITTEST_DISABLED_DECORATORS:
            if dotted_name in {f"{alias}.{decorator_name}", f"{alias}.case.{decorator_name}"}:
                return decorator_name

    for alias in alias_state.unittest_case_aliases:
        for decorator_name in _UNITTEST_DISABLED_DECORATORS:
            if dotted_name == f"{alias}.{decorator_name}":
                return decorator_name

    return None


def _decorator_condition_disables_target(
    decorator: ast.expr,
    *,
    disabled_when: bool,
) -> bool:
    condition_truthiness = _resolve_static_condition_truthiness(decorator)
    if condition_truthiness is None:
        return True
    return condition_truthiness is disabled_when


def _resolve_static_condition_truthiness(decorator: ast.expr) -> bool | None:
    if not isinstance(decorator, ast.Call):
        return None

    if decorator.args:
        return _static_truthiness(decorator.args[0])

    for keyword in decorator.keywords:
        if keyword.arg == "condition":
            return _static_truthiness(keyword.value)
    return None


def _static_truthiness(expression: ast.expr) -> bool | None:
    if isinstance(expression, ast.Constant):
        return bool(expression.value)
    if isinstance(expression, (ast.Tuple, ast.List, ast.Set)):
        if not all(_is_static_literal(element) for element in expression.elts):
            return None
        return bool(expression.elts)
    if isinstance(expression, ast.Dict):
        if not all(
            key is not None and _is_static_literal(key) and _is_static_literal(value)
            for key, value in zip(expression.keys, expression.values, strict=True)
        ):
            return None
        return bool(expression.keys)
    if isinstance(expression, ast.UnaryOp):
        operand_truthiness = _static_truthiness(expression.operand)
        if operand_truthiness is None:
            return None
        if isinstance(expression.op, ast.Not):
            return not operand_truthiness
        if isinstance(expression.op, (ast.UAdd, ast.USub)) and isinstance(
            expression.operand, ast.Constant
        ):
            operand_value = expression.operand.value
            if not isinstance(operand_value, (int, float, complex)):
                return None
            numeric_value = (
                operand_value if isinstance(expression.op, ast.UAdd) else -operand_value
            )
            return bool(numeric_value)
    return None


def _is_static_literal(expression: ast.expr) -> bool:
    if isinstance(expression, ast.Constant):
        return True
    if isinstance(expression, ast.UnaryOp) and isinstance(expression.op, (ast.UAdd, ast.USub)):
        return isinstance(expression.operand, ast.Constant) and isinstance(
            expression.operand.value,
            (int, float, complex),
        )
    if isinstance(expression, (ast.Tuple, ast.List, ast.Set)):
        return all(_is_static_literal(element) for element in expression.elts)
    if isinstance(expression, ast.Dict):
        return all(
            key is not None and _is_static_literal(key) and _is_static_literal(value)
            for key, value in zip(expression.keys, expression.values, strict=True)
        )
    return False


def _new_alias_state() -> _DecoratorAliasState:
    return _DecoratorAliasState(
        pytest_module_aliases=set(),
        unittest_module_aliases=set(),
        unittest_case_aliases=set(),
        unittest_skip_names={},
    )


def _copy_alias_state(alias_state: _DecoratorAliasState) -> _DecoratorAliasState:
    return _DecoratorAliasState(
        pytest_module_aliases=set(alias_state.pytest_module_aliases),
        unittest_module_aliases=set(alias_state.unittest_module_aliases),
        unittest_case_aliases=set(alias_state.unittest_case_aliases),
        unittest_skip_names=dict(alias_state.unittest_skip_names),
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
        unittest_skip_names={
            name: decorator_name
            for name, decorator_name in left.unittest_skip_names.items()
            if right.unittest_skip_names.get(name) == decorator_name
        },
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
                alias_state.unittest_skip_names[bound_name] = alias.name
            elif alias.name == "case":
                alias_state.unittest_case_aliases.add(bound_name)
        return

    if statement.module == "unittest.case":
        for alias in statement.names:
            if alias.name in _UNITTEST_DISABLED_DECORATORS:
                alias_state.unittest_skip_names[alias.asname or alias.name] = alias.name


def _discard_aliases(
    rebound_names: set[str],
    alias_state: _DecoratorAliasState,
) -> None:
    alias_state.pytest_module_aliases.difference_update(rebound_names)
    alias_state.unittest_module_aliases.difference_update(rebound_names)
    alias_state.unittest_case_aliases.difference_update(rebound_names)
    for name in rebound_names:
        alias_state.unittest_skip_names.pop(name, None)


def _collect_rebound_names(statement: ast.stmt) -> set[str]:
    if isinstance(statement, ast.Assign):
        names: set[str] = set()
        for target in statement.targets:
            names.update(_collect_target_names(target))
        names.update(_collect_named_expr_names(statement.value))
        return names
    if isinstance(statement, (ast.AnnAssign, ast.AugAssign)):
        names = _collect_target_names(statement.target)
        if statement.value is not None:
            names.update(_collect_named_expr_names(statement.value))
        return names
    if isinstance(statement, ast.Delete):
        names: set[str] = set()
        for target in statement.targets:
            names.update(_collect_target_names(target))
        return names
    if isinstance(statement, ast.Expr):
        return _collect_named_expr_names(statement.value)
    if isinstance(statement, (ast.If, ast.While)):
        return _collect_named_expr_names(statement.test)
    if isinstance(statement, (ast.For, ast.AsyncFor)):
        names = _collect_target_names(statement.target)
        names.update(_collect_named_expr_names(statement.iter))
        return names
    if isinstance(statement, (ast.With, ast.AsyncWith)):
        names: set[str] = set()
        for item in statement.items:
            if item.optional_vars is not None:
                names.update(_collect_target_names(item.optional_vars))
            names.update(_collect_named_expr_names(item.context_expr))
        return names
    if isinstance(statement, ast.Match):
        names = _collect_named_expr_names(statement.subject)
        for case in statement.cases:
            if case.guard is not None:
                names.update(_collect_named_expr_names(case.guard))
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


def _collect_named_expr_names(node: ast.AST) -> set[str]:
    names: set[str] = set()
    stack: list[ast.AST] = [node]

    while stack:
        current = stack.pop()
        if isinstance(current, ast.NamedExpr):
            names.update(_collect_target_names(current.target))
            stack.append(current.value)
            continue
        if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
            continue
        children = list(ast.iter_child_nodes(current))
        for child in reversed(children):
            stack.append(child)

    return names


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
