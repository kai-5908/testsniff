from __future__ import annotations

import ast

from testsniff.parser.ast_index import FunctionNode


def iter_executable_body(function: FunctionNode) -> tuple[ast.stmt, ...]:
    body = tuple(function.body)
    if body and _is_string_literal_expr(body[0]):
        return body[1:]
    return body


def is_effectively_empty(function: FunctionNode) -> bool:
    body = iter_executable_body(function)
    if not body:
        return True
    return len(body) == 1 and isinstance(body[0], ast.Pass)


def _is_string_literal_expr(statement: ast.stmt) -> bool:
    if not isinstance(statement, ast.Expr):
        return False
    return isinstance(statement.value, ast.Constant) and isinstance(statement.value.value, str)
