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
            unittest_aliases, testcase_aliases = _collect_import_aliases(tree)
            testcase_class_names = _collect_testcase_class_names(
                tree,
                unittest_aliases=unittest_aliases,
                testcase_aliases=testcase_aliases,
            )
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


def _collect_import_aliases(tree: ast.Module) -> tuple[set[str], set[str]]:
    unittest_aliases: set[str] = set()
    testcase_aliases: set[str] = set()

    for statement in tree.body:
        if isinstance(statement, ast.Import):
            for alias in statement.names:
                if alias.name == "unittest":
                    unittest_aliases.add(alias.asname or alias.name)
        elif isinstance(statement, ast.ImportFrom) and statement.module in {
            "unittest",
            "unittest.case",
        }:
            for alias in statement.names:
                if alias.name == "TestCase":
                    testcase_aliases.add(alias.asname or alias.name)

    return unittest_aliases, testcase_aliases


def _collect_testcase_class_names(
    tree: ast.Module,
    *,
    unittest_aliases: set[str],
    testcase_aliases: set[str],
) -> set[str]:
    classes = [statement for statement in tree.body if isinstance(statement, ast.ClassDef)]
    class_names = {class_node.name for class_node in classes}
    dependents: dict[str, set[str]] = {class_node.name: set() for class_node in classes}
    testcase_class_names: set[str] = set()

    for class_node in classes:
        for base in class_node.bases:
            base_reference = _resolve_base_reference(
                base,
                unittest_aliases=unittest_aliases,
                testcase_aliases=testcase_aliases,
                class_names=class_names,
            )
            if base_reference is None:
                continue
            if base_reference == TESTCASE_ROOT:
                testcase_class_names.add(class_node.name)
                continue
            dependents[base_reference].add(class_node.name)

    queue = deque(testcase_class_names)
    while queue:
        base_class_name = queue.popleft()
        for derived_class_name in dependents.get(base_class_name, ()):
            if derived_class_name in testcase_class_names:
                continue
            testcase_class_names.add(derived_class_name)
            queue.append(derived_class_name)

    return testcase_class_names


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

        if not isinstance(statement, ast.ClassDef) or statement.name not in testcase_class_names:
            continue

        for member in statement.body:
            if isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef)) and _is_test_name(
                member.name
            ):
                targets.append(
                    TestTarget(node=member, style="unittest", class_name=statement.name)
                )

    return targets


def _resolve_base_reference(
    base: ast.expr,
    *,
    unittest_aliases: set[str],
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
