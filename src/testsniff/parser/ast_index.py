from __future__ import annotations

import ast
from collections import deque
from dataclasses import dataclass
from typing import Literal

FunctionNode = ast.FunctionDef | ast.AsyncFunctionDef
TESTCASE_ROOT = "__testsniff_unittest_testcase_root__"


@dataclass(slots=True, frozen=True)
class TestTarget:
    node: FunctionNode
    style: Literal["pytest", "unittest"]
    class_name: str | None = None


@dataclass(slots=True)
class ASTIndex:
    functions: tuple[FunctionNode, ...]
    classes: tuple[ast.ClassDef, ...]
    test_targets: tuple[TestTarget, ...]

    @classmethod
    def from_tree(cls, tree: ast.AST) -> ASTIndex:
        functions: list[FunctionNode] = []
        classes: list[ast.ClassDef] = []
        test_targets: list[TestTarget] = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions.append(node)
            elif isinstance(node, ast.ClassDef):
                classes.append(node)

        if isinstance(tree, ast.Module):
            testcase_class_names = _collect_testcase_class_names(tree)
            test_targets.extend(
                _collect_test_targets(
                    tree,
                    testcase_class_names=testcase_class_names,
                )
            )

        return cls(
            functions=tuple(functions),
            classes=tuple(classes),
            test_targets=tuple(test_targets),
        )


def _collect_testcase_class_names(tree: ast.Module) -> set[str]:
    classes = [statement for statement in tree.body if isinstance(statement, ast.ClassDef)]
    class_names = {class_node.name for class_node in classes}
    dependents: dict[str, set[str]] = {class_node.name: set() for class_node in classes}
    testcase_class_names: set[str] = set()
    unittest_aliases: set[str] = set()
    unittest_case_aliases: set[str] = set()
    testcase_aliases: set[str] = set()

    for statement in tree.body:
        if isinstance(statement, ast.ClassDef):
            for base in statement.bases:
                base_reference = _resolve_base_reference(
                    base,
                    unittest_aliases=unittest_aliases,
                    unittest_case_aliases=unittest_case_aliases,
                    testcase_aliases=testcase_aliases,
                    class_names=class_names,
                )
                if base_reference is None:
                    continue
                if base_reference == TESTCASE_ROOT:
                    testcase_class_names.add(statement.name)
                    continue
                dependents[base_reference].add(statement.name)
            _discard_rebound_aliases(
                {statement.name}, unittest_aliases, unittest_case_aliases, testcase_aliases
            )
            continue

        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
            _discard_rebound_aliases(
                {statement.name}, unittest_aliases, unittest_case_aliases, testcase_aliases
            )
            continue

        if isinstance(statement, (ast.Import, ast.ImportFrom)):
            _update_import_aliases(
                statement,
                unittest_aliases=unittest_aliases,
                unittest_case_aliases=unittest_case_aliases,
                testcase_aliases=testcase_aliases,
            )
            continue

        rebound_names = _collect_rebound_names(statement)
        if rebound_names:
            _discard_rebound_aliases(
                rebound_names, unittest_aliases, unittest_case_aliases, testcase_aliases
            )

    queue = deque(testcase_class_names)
    while queue:
        base_class_name = queue.popleft()
        for derived_class_name in dependents.get(base_class_name, ()):
            if derived_class_name in testcase_class_names:
                continue
            testcase_class_names.add(derived_class_name)
            queue.append(derived_class_name)

    return testcase_class_names


def _update_import_aliases(
    statement: ast.Import | ast.ImportFrom,
    *,
    unittest_aliases: set[str],
    unittest_case_aliases: set[str],
    testcase_aliases: set[str],
) -> None:
    bound_names = {alias.asname or alias.name.split(".")[0] for alias in statement.names}
    _discard_rebound_aliases(bound_names, unittest_aliases, unittest_case_aliases, testcase_aliases)

    if isinstance(statement, ast.Import):
        for alias in statement.names:
            if alias.name == "unittest":
                unittest_aliases.add(alias.asname or alias.name)
            elif alias.name == "unittest.case":
                unittest_case_aliases.add(alias.asname or alias.name)
        return

    if statement.module not in {"unittest", "unittest.case"}:
        return

    for alias in statement.names:
        if alias.name == "TestCase":
            testcase_aliases.add(alias.asname or alias.name)
        elif statement.module == "unittest" and alias.name == "case":
            unittest_case_aliases.add(alias.asname or alias.name)


def _discard_rebound_aliases(
    rebound_names: set[str],
    unittest_aliases: set[str],
    unittest_case_aliases: set[str],
    testcase_aliases: set[str],
) -> None:
    unittest_aliases.difference_update(rebound_names)
    unittest_case_aliases.difference_update(rebound_names)
    testcase_aliases.difference_update(rebound_names)


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


def _collect_test_targets(
    tree: ast.Module,
    *,
    testcase_class_names: set[str],
) -> list[TestTarget]:
    targets: list[TestTarget] = []

    for statement in tree.body:
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if _is_test_name(statement.name):
                targets.append(TestTarget(node=statement, style="pytest"))
            continue

        if not isinstance(statement, ast.ClassDef):
            continue

        if statement.name in testcase_class_names:
            style: Literal["pytest", "unittest"] = "unittest"
        elif _is_pytest_test_class(statement):
            style = "pytest"
        else:
            continue

        for member in statement.body:
            if isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef)) and _is_test_name(
                member.name
            ):
                targets.append(TestTarget(node=member, style=style, class_name=statement.name))

    return targets


def _resolve_base_reference(
    base: ast.expr,
    *,
    unittest_aliases: set[str],
    unittest_case_aliases: set[str],
    testcase_aliases: set[str],
    class_names: set[str],
) -> str | None:
    if isinstance(base, ast.Name):
        if base.id in testcase_aliases:
            return TESTCASE_ROOT
        if base.id in class_names:
            return base.id
        return None

    dotted_name = _as_dotted_name(base)
    if dotted_name is None:
        return None
    if dotted_name in {"unittest.TestCase", "unittest.case.TestCase"}:
        return TESTCASE_ROOT
    if any(
        dotted_name in {f"{alias}.TestCase", f"{alias}.case.TestCase"}
        for alias in unittest_aliases
    ):
        return TESTCASE_ROOT
    if any(dotted_name == f"{alias}.TestCase" for alias in unittest_case_aliases):
        return TESTCASE_ROOT
    return None


def _as_dotted_name(node: ast.expr) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _as_dotted_name(node.value)
        if parent is None:
            return None
        return f"{parent}.{node.attr}"
    return None


def _is_test_name(name: str) -> bool:
    return name.startswith("test_")


def _is_pytest_test_class(class_node: ast.ClassDef) -> bool:
    if not class_node.name.startswith("Test"):
        return False
    if any(
        isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef))
        and member.name in {"__init__", "__new__"}
        for member in class_node.body
    ):
        return False
    return not _has_pytest_opt_out(class_node)


def _has_pytest_opt_out(class_node: ast.ClassDef) -> bool:
    for member in class_node.body:
        if not isinstance(member, ast.Assign):
            continue
        if len(member.targets) != 1 or not isinstance(member.targets[0], ast.Name):
            continue
        if member.targets[0].id != "__test__":
            continue
        return _is_false_constant(member.value)
    return False


def _is_false_constant(node: ast.expr) -> bool:
    return isinstance(node, ast.Constant) and node.value is False
