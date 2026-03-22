from __future__ import annotations

import ast
from pathlib import Path

from testsniff.parser.module_context import ModuleContext
from testsniff.rules.checks import _comment_placeholder as placeholder


def test_has_leading_docstring_rejects_empty_body() -> None:
    assert placeholder.has_leading_docstring([]) is False


def test_collect_comments_only_placeholder_targets_ignores_comments_outside_function_body() -> None:
    module = ModuleContext.from_source(
        Path("tests/test_comments_outside_body.py"),
        """
def test_first():
    \"\"\"Documented body.\"\"\"

# Not part of the preceding test body.
def test_second():
    assert True
""".strip(),
    )

    assert placeholder.collect_comments_only_placeholder_targets(module) == frozenset()


def test_same_line_body_comment_requires_comment_on_first_statement_line() -> None:
    function = ast.parse(
        """
def test_example():
    pass
""".strip(),
        mode="exec",
    ).body[0]
    module = ModuleContext.from_source(
        Path("tests/test_comment_tokens.py"),
        """
def test_example():
    pass
    # later comment
""".strip(),
    )
    token = next(token for token in module.tokens if token.string == "# later comment")

    assert placeholder._is_same_line_body_comment(token, function) is False


def test_first_body_line_falls_back_to_function_line_for_synthetic_empty_body() -> None:
    function = ast.FunctionDef(
        name="test_example",
        args=ast.arguments(
            posonlyargs=[],
            args=[],
            vararg=None,
            kwonlyargs=[],
            kw_defaults=[],
            kwarg=None,
            defaults=[],
        ),
        body=[],
        decorator_list=[],
        returns=None,
        type_comment=None,
        lineno=7,
        col_offset=0,
    )

    assert placeholder._first_body_line(function) == 7
