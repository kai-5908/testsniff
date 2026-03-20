from __future__ import annotations

import ast
from tokenize import COMMENT, TokenInfo

from testsniff.parser.module_context import ModuleContext

FunctionNode = ast.FunctionDef | ast.AsyncFunctionDef


def strip_leading_docstring(function: FunctionNode) -> list[ast.stmt]:
    body = list(function.body)
    if has_leading_docstring(body):
        return body[1:]
    return body


def has_leading_docstring(body: list[ast.stmt]) -> bool:
    if not body:
        return False
    first = body[0]
    if not isinstance(first, ast.Expr):
        return False
    return isinstance(first.value, ast.Constant) and isinstance(first.value.value, str)


def is_comments_only_placeholder_test(module: ModuleContext, function: FunctionNode) -> bool:
    return not strip_leading_docstring(function) and _has_comment_token_in_body(module, function)


def _has_comment_token_in_body(module: ModuleContext, function: FunctionNode) -> bool:
    suite_end_line = _find_suite_end_line(module.source_text, function)
    return any(
        _is_comment_in_function_body(token, function, suite_end_line) for token in module.tokens
    )


def _find_suite_end_line(source_text: str, function: FunctionNode) -> int:
    # Function AST spans stop at the last statement, so trailing body comments need line scanning.
    for lineno, line in enumerate(source_text.splitlines(), start=1):
        if lineno <= function.lineno:
            continue
        stripped = line.lstrip()
        if not stripped:
            continue
        indent = len(line) - len(stripped)
        if indent <= function.col_offset:
            return lineno - 1
    return len(source_text.splitlines())


def _is_comment_in_function_body(
    token: TokenInfo,
    function: FunctionNode,
    suite_end_line: int,
) -> bool:
    if token.type != COMMENT:
        return False
    line, column = token.start
    return function.lineno < line <= suite_end_line and column > function.col_offset
