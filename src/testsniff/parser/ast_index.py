from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import Literal

FunctionNode = ast.FunctionDef | ast.AsyncFunctionDef


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
    testcase_class_names: set[str] = set()
    classes = [statement for statement in tree.body if isinstance(statement, ast.ClassDef)]

    changed = True
    while changed:
        changed = False
        for class_node in classes:
            if class_node.name in testcase_class_names:
                continue
            if any(
                _is_testcase_base(
                    base,
                    unittest_aliases=unittest_aliases,
                    testcase_aliases=testcase_aliases,
                    testcase_class_names=testcase_class_names,
                )
                for base in class_node.bases
            ):
                testcase_class_names.add(class_node.name)
                changed = True

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


def _is_testcase_base(
    base: ast.expr,
    *,
    unittest_aliases: set[str],
    testcase_aliases: set[str],
    testcase_class_names: set[str],
) -> bool:
    if isinstance(base, ast.Name):
        return base.id in testcase_aliases or base.id in testcase_class_names

    dotted_name = _as_dotted_name(base)
    if dotted_name is None:
        return False
    if dotted_name in {"unittest.TestCase", "unittest.case.TestCase"}:
        return True
    return any(
        dotted_name in {f"{alias}.TestCase", f"{alias}.case.TestCase"}
        for alias in unittest_aliases
    )


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
