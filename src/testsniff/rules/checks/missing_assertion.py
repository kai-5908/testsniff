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

    return _block_has_recognized_assertion(
        iter_executable_body(target.node),
        unittest_receiver_name=receiver_name if target.style == "unittest" else None,
        pytest_aliases=active_aliases,
    )


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


def _block_has_recognized_assertion(
    statements: tuple[ast.stmt, ...] | list[ast.stmt],
    *,
    unittest_receiver_name: str | None,
    pytest_aliases: _TargetPytestAliases,
) -> bool:
    for statement in statements:
        if _statement_has_recognized_assertion(
            statement,
            unittest_receiver_name=unittest_receiver_name,
            pytest_aliases=pytest_aliases,
        ):
            return True
    return False


def _copy_pytest_aliases(pytest_aliases: _TargetPytestAliases) -> _TargetPytestAliases:
    return _TargetPytestAliases(
        module_aliases=set(pytest_aliases.module_aliases),
        helper_names=set(pytest_aliases.helper_names),
    )


def _overwrite_pytest_aliases(
    target: _TargetPytestAliases,
    source: _TargetPytestAliases,
) -> None:
    target.module_aliases.clear()
    target.module_aliases.update(source.module_aliases)
    target.helper_names.clear()
    target.helper_names.update(source.helper_names)


def _merge_pytest_aliases_intersection(
    left: _TargetPytestAliases,
    right: _TargetPytestAliases,
) -> _TargetPytestAliases:
    return _TargetPytestAliases(
        module_aliases=left.module_aliases & right.module_aliases,
        helper_names=left.helper_names & right.helper_names,
    )


def _merge_pytest_aliases_union(
    left: _TargetPytestAliases,
    right: _TargetPytestAliases,
) -> _TargetPytestAliases:
    return _TargetPytestAliases(
        module_aliases=left.module_aliases | right.module_aliases,
        helper_names=left.helper_names | right.helper_names,
    )


def _statement_has_recognized_assertion(
    statement: ast.stmt,
    *,
    unittest_receiver_name: str | None,
    pytest_aliases: _TargetPytestAliases,
) -> bool:
    if isinstance(statement, ast.Assert):
        return True

    if _statement_header_has_recognized_assertion(
        statement,
        unittest_receiver_name=unittest_receiver_name,
        pytest_aliases=pytest_aliases,
    ):
        return True

    if isinstance(statement, ast.Import):
        _apply_import_alias_updates(statement, pytest_aliases)
        return False

    if isinstance(statement, ast.ImportFrom):
        _apply_import_from_alias_updates(statement, pytest_aliases)
        return False

    if isinstance(statement, ast.With | ast.AsyncWith):
        body_aliases = _copy_pytest_aliases(pytest_aliases)
        _discard_pytest_aliases(
            _collect_with_optional_var_names(statement),
            body_aliases.module_aliases,
            body_aliases.helper_names,
        )
        if _block_has_recognized_assertion(
            statement.body,
            unittest_receiver_name=unittest_receiver_name,
            pytest_aliases=body_aliases,
        ):
            return True
        _overwrite_pytest_aliases(pytest_aliases, body_aliases)
        return False

    if isinstance(statement, ast.For | ast.AsyncFor):
        body_aliases = _copy_pytest_aliases(pytest_aliases)
        _discard_pytest_aliases(
            _collect_target_names(statement.target),
            body_aliases.module_aliases,
            body_aliases.helper_names,
        )
        if _block_has_recognized_assertion(
            statement.body,
            unittest_receiver_name=unittest_receiver_name,
            pytest_aliases=body_aliases,
        ):
            return True
        loop_aliases = _copy_pytest_aliases(body_aliases)
        if _block_has_recognized_assertion(
            statement.orelse,
            unittest_receiver_name=unittest_receiver_name,
            pytest_aliases=loop_aliases,
        ):
            return True
        _overwrite_pytest_aliases(pytest_aliases, loop_aliases)
        return False

    if isinstance(statement, ast.Try):
        body_aliases = _copy_pytest_aliases(pytest_aliases)
        if _block_has_recognized_assertion(
            statement.body,
            unittest_receiver_name=unittest_receiver_name,
            pytest_aliases=body_aliases,
        ):
            return True
        orelse_aliases = _copy_pytest_aliases(body_aliases)
        if _block_has_recognized_assertion(
            statement.orelse,
            unittest_receiver_name=unittest_receiver_name,
            pytest_aliases=orelse_aliases,
        ):
            return True
        finally_start_aliases = _merge_pytest_aliases_union(body_aliases, orelse_aliases)
        if _block_has_recognized_assertion(
            statement.finalbody,
            unittest_receiver_name=unittest_receiver_name,
            pytest_aliases=finally_start_aliases,
        ):
            return True
        handler_aliases_to_merge: list[_TargetPytestAliases] = []
        for handler in statement.handlers:
            if handler.type is not None and _expression_has_recognized_assertion(
                handler.type,
                unittest_receiver_name=unittest_receiver_name,
                pytest_aliases=pytest_aliases,
            ):
                return True
            handler_aliases = _copy_pytest_aliases(pytest_aliases)
            if handler.name is not None:
                _discard_pytest_aliases(
                    {handler.name},
                    handler_aliases.module_aliases,
                    handler_aliases.helper_names,
                )
            if _block_has_recognized_assertion(
                handler.body,
                unittest_receiver_name=unittest_receiver_name,
                    pytest_aliases=handler_aliases,
            ):
                return True
            handler_aliases_to_merge.append(handler_aliases)
        for handler_aliases in handler_aliases_to_merge:
            finally_start_aliases = _merge_pytest_aliases_union(
                finally_start_aliases,
                handler_aliases,
            )
        _overwrite_pytest_aliases(pytest_aliases, finally_start_aliases)
        return False

    if isinstance(statement, ast.If):
        body_aliases = _copy_pytest_aliases(pytest_aliases)
        if _block_has_recognized_assertion(
            statement.body,
            unittest_receiver_name=unittest_receiver_name,
            pytest_aliases=body_aliases,
        ):
            return True
        else_aliases = _copy_pytest_aliases(pytest_aliases)
        if _block_has_recognized_assertion(
            statement.orelse,
            unittest_receiver_name=unittest_receiver_name,
            pytest_aliases=else_aliases,
        ):
            return True
        if _is_static_truthy(statement.test):
            _overwrite_pytest_aliases(pytest_aliases, body_aliases)
        elif _is_static_falsy(statement.test):
            _overwrite_pytest_aliases(pytest_aliases, else_aliases)
        else:
            _overwrite_pytest_aliases(
                pytest_aliases,
                _merge_pytest_aliases_intersection(body_aliases, else_aliases),
            )
        return False

    if isinstance(statement, ast.While):
        body_aliases = _copy_pytest_aliases(pytest_aliases)
        if _block_has_recognized_assertion(
            statement.body,
            unittest_receiver_name=unittest_receiver_name,
            pytest_aliases=body_aliases,
        ):
            return True
        else_aliases = _copy_pytest_aliases(pytest_aliases)
        if _block_has_recognized_assertion(
            statement.orelse,
            unittest_receiver_name=unittest_receiver_name,
            pytest_aliases=else_aliases,
        ):
            return True
        if _is_static_falsy(statement.test):
            _overwrite_pytest_aliases(pytest_aliases, else_aliases)
        else:
            _overwrite_pytest_aliases(
                pytest_aliases,
                _merge_pytest_aliases_intersection(body_aliases, else_aliases),
            )
        return False

    if isinstance(statement, ast.Match):
        case_end_aliases: list[_TargetPytestAliases] = []
        for case in statement.cases:
            case_aliases = _copy_pytest_aliases(pytest_aliases)
            _discard_pytest_aliases(
                _collect_pattern_capture_names(case.pattern),
                case_aliases.module_aliases,
                case_aliases.helper_names,
            )
            if case.guard is not None and _expression_has_recognized_assertion(
                case.guard,
                unittest_receiver_name=unittest_receiver_name,
                pytest_aliases=case_aliases,
            ):
                return True
            if _block_has_recognized_assertion(
                case.body,
                unittest_receiver_name=unittest_receiver_name,
                pytest_aliases=case_aliases,
            ):
                return True
            case_end_aliases.append(case_aliases)
        if case_end_aliases:
            merged_aliases = case_end_aliases[0]
            for case_aliases in case_end_aliases[1:]:
                merged_aliases = _merge_pytest_aliases_intersection(
                    merged_aliases,
                    case_aliases,
                )
            _overwrite_pytest_aliases(pytest_aliases, merged_aliases)
        return False

    if isinstance(statement, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
        _discard_pytest_aliases(
            {statement.name},
            pytest_aliases.module_aliases,
            pytest_aliases.helper_names,
        )
        return False

    rebound_names = _collect_rebound_names(statement)
    if rebound_names:
        _discard_pytest_aliases(
            rebound_names,
            pytest_aliases.module_aliases,
            pytest_aliases.helper_names,
        )
    return False


def _statement_header_has_recognized_assertion(
    statement: ast.stmt,
    pytest_aliases: _TargetPytestAliases,
    *,
    unittest_receiver_name: str | None,
) -> bool:
    for expression in _iter_statement_header_expressions(statement):
        if _expression_has_recognized_assertion(
            expression,
            unittest_receiver_name=unittest_receiver_name,
            pytest_aliases=pytest_aliases,
        ):
            return True
    return False


def _iter_statement_header_expressions(statement: ast.stmt) -> tuple[ast.AST, ...]:
    if isinstance(statement, ast.Expr):
        return (statement.value,)
    if isinstance(statement, ast.Assign):
        return (statement.value,)
    if isinstance(statement, ast.AnnAssign):
        if statement.value is None:
            return ()
        return (statement.value,)
    if isinstance(statement, ast.AugAssign):
        return (statement.value,)
    if isinstance(statement, ast.Return):
        if statement.value is None:
            return ()
        return (statement.value,)
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


def _expression_has_recognized_assertion(
    expression: ast.AST,
    *,
    unittest_receiver_name: str | None,
    pytest_aliases: _TargetPytestAliases,
) -> bool:
    stack: list[ast.AST] = [expression]

    while stack:
        node = stack.pop()
        if isinstance(node, ast.Call) and (
            _is_unittest_assertion_call(node, unittest_receiver_name)
            or _is_pytest_assertion_call(node, pytest_aliases)
        ):
            return True
        if isinstance(node, ast.Lambda):
            continue
        children = list(ast.iter_child_nodes(node))
        for child in reversed(children):
            stack.append(child)

    return False


def _apply_import_alias_updates(
    statement: ast.Import,
    pytest_aliases: _TargetPytestAliases,
) -> None:
    _discard_pytest_aliases(
        {alias.asname or alias.name.split(".")[0] for alias in statement.names},
        pytest_aliases.module_aliases,
        pytest_aliases.helper_names,
    )
    for alias in statement.names:
        if alias.name == "pytest":
            pytest_aliases.module_aliases.add(alias.asname or alias.name)


def _apply_import_from_alias_updates(
    statement: ast.ImportFrom,
    pytest_aliases: _TargetPytestAliases,
) -> None:
    _discard_pytest_aliases(
        {alias.asname or alias.name for alias in statement.names},
        pytest_aliases.module_aliases,
        pytest_aliases.helper_names,
    )
    if statement.module == "pytest":
        for alias in statement.names:
            if alias.name in _PYTEST_HELPERS:
                pytest_aliases.helper_names.add(alias.asname or alias.name)


def _collect_with_optional_var_names(statement: ast.With | ast.AsyncWith) -> set[str]:
    names: set[str] = set()
    for item in statement.items:
        if item.optional_vars is not None:
            names.update(_collect_target_names(item.optional_vars))
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
