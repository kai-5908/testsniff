from __future__ import annotations

import ast
from dataclasses import dataclass


@dataclass(slots=True)
class ASTIndex:
    functions: tuple[ast.FunctionDef | ast.AsyncFunctionDef, ...]
    classes: tuple[ast.ClassDef, ...]

    @classmethod
    def from_tree(cls, tree: ast.AST) -> ASTIndex:
        functions: list[ast.FunctionDef | ast.AsyncFunctionDef] = []
        classes: list[ast.ClassDef] = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions.append(node)
            elif isinstance(node, ast.ClassDef):
                classes.append(node)
        return cls(functions=tuple(functions), classes=tuple(classes))
