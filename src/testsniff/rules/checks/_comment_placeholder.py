from __future__ import annotations

import ast
from bisect import bisect_left, bisect_right
from tokenize import COMMENT, TokenInfo

from testsniff.parser.ast_index import TestTarget
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


def collect_comments_only_placeholder_targets(module: ModuleContext) -> frozenset[FunctionNode]:
    comment_tokens_by_line = _collect_comment_tokens_by_line(module.tokens)
    if not comment_tokens_by_line:
        return frozenset()

    comment_lines = tuple(sorted(comment_tokens_by_line))
    placeholders: set[FunctionNode] = set()
    for target in module.index.test_targets:
        function = target.node
        if strip_leading_docstring(function):
            continue
        if _has_comment_token_in_body(target, comment_lines, comment_tokens_by_line):
            placeholders.add(function)
    return frozenset(placeholders)


def _collect_comment_tokens_by_line(
    tokens: tuple[TokenInfo, ...],
) -> dict[int, tuple[TokenInfo, ...]]:
    comments_by_line: dict[int, list[TokenInfo]] = {}
    for token in tokens:
        if token.type != COMMENT:
            continue
        comments_by_line.setdefault(token.start[0], []).append(token)
    return {line: tuple(line_tokens) for line, line_tokens in comments_by_line.items()}


def _has_comment_token_in_body(
    target: TestTarget,
    comment_lines: tuple[int, ...],
    comment_tokens_by_line: dict[int, tuple[TokenInfo, ...]],
) -> bool:
    function = target.node
    body_start_line = _first_body_line(function)

    same_line_tokens = comment_tokens_by_line.get(body_start_line, ())
    if any(_is_same_line_body_comment(token, function) for token in same_line_tokens):
        return True

    if target.body_end_line <= body_start_line:
        return False

    start_index = bisect_left(comment_lines, body_start_line + 1)
    end_index = bisect_right(comment_lines, target.body_end_line)
    for line_number in comment_lines[start_index:end_index]:
        if any(
            token.start[1] > function.col_offset
            for token in comment_tokens_by_line[line_number]
        ):
            return True
    return False


def _is_same_line_body_comment(
    token: TokenInfo,
    function: FunctionNode,
) -> bool:
    first_statement = function.body[0]
    statement_end_column = first_statement.end_col_offset
    line, column = token.start
    if line != first_statement.lineno or statement_end_column is None:
        return False
    return column >= statement_end_column


def _first_body_line(function: FunctionNode) -> int:
    if not function.body:
        return function.lineno
    return function.body[0].lineno
