from __future__ import annotations

import ast
import textwrap

import testsniff.rules.checks.duplicate_assert as duplicate_assert


def test_statement_duplicate_assertion_handles_with_if_loop_while_and_match_branches() -> None:
    bare_key = _bare_assert_key("value == 1")

    with_seen: set[duplicate_assert._AssertionKey] = {bare_key}
    assert (
        duplicate_assert._statement_has_duplicate_assertion(
            _statement("with manager():\n    assert value == 1"),
            seen_assertions=with_seen,
            unittest_receiver_name=None,
        )
        is True
    )

    with_propagated: set[duplicate_assert._AssertionKey] = set()
    assert (
        duplicate_assert._statement_has_duplicate_assertion(
            _statement("with manager():\n    assert value == 1"),
            seen_assertions=with_propagated,
            unittest_receiver_name=None,
        )
        is False
    )
    assert with_propagated == {bare_key}

    body_duplicate_seen: set[duplicate_assert._AssertionKey] = {bare_key}
    assert (
        duplicate_assert._statement_has_duplicate_assertion(
            _statement(
                """
if condition:
    assert value == 1
else:
    pass
""".strip()
            ),
            seen_assertions=body_duplicate_seen,
            unittest_receiver_name=None,
        )
        is True
    )

    static_false_if_seen: set[duplicate_assert._AssertionKey] = set()
    assert (
        duplicate_assert._statement_has_duplicate_assertion(
            _statement(
                """
if False:
    pass
else:
    assert value == 1
""".strip()
            ),
            seen_assertions=static_false_if_seen,
            unittest_receiver_name=None,
        )
        is False
    )
    assert static_false_if_seen == {bare_key}

    else_duplicate_seen: set[duplicate_assert._AssertionKey] = {bare_key}
    assert (
        duplicate_assert._statement_has_duplicate_assertion(
            _statement(
                """
if condition:
    pass
else:
    assert value == 1
""".strip()
            ),
            seen_assertions=else_duplicate_seen,
            unittest_receiver_name=None,
        )
        is True
    )

    for_duplicate_seen: set[duplicate_assert._AssertionKey] = {bare_key}
    assert (
        duplicate_assert._statement_has_duplicate_assertion(
            _statement("for item in items:\n    assert value == 1"),
            seen_assertions=for_duplicate_seen,
            unittest_receiver_name=None,
        )
        is True
    )

    for_else_duplicate_seen: set[duplicate_assert._AssertionKey] = {bare_key}
    assert (
        duplicate_assert._statement_has_duplicate_assertion(
            _statement(
                """
for item in items:
    pass
else:
    assert value == 1
""".strip()
            ),
            seen_assertions=for_else_duplicate_seen,
            unittest_receiver_name=None,
        )
        is True
    )
    for_no_duplicate_seen: set[duplicate_assert._AssertionKey] = set()
    assert (
        duplicate_assert._statement_has_duplicate_assertion(
            _statement(
                """
for item in items:
    pass
else:
    pass
""".strip()
            ),
            seen_assertions=for_no_duplicate_seen,
            unittest_receiver_name=None,
        )
        is False
    )

    while_body_duplicate_seen: set[duplicate_assert._AssertionKey] = {bare_key}
    assert (
        duplicate_assert._statement_has_duplicate_assertion(
            _statement("while condition:\n    assert value == 1"),
            seen_assertions=while_body_duplicate_seen,
            unittest_receiver_name=None,
        )
        is True
    )

    while_false_seen: set[duplicate_assert._AssertionKey] = set()
    assert (
        duplicate_assert._statement_has_duplicate_assertion(
            _statement(
                """
while False:
    pass
else:
    assert value == 1
""".strip()
            ),
            seen_assertions=while_false_seen,
            unittest_receiver_name=None,
        )
        is False
    )
    assert while_false_seen == {bare_key}

    while_else_duplicate_seen: set[duplicate_assert._AssertionKey] = {bare_key}
    assert (
        duplicate_assert._statement_has_duplicate_assertion(
            _statement(
                """
while condition:
    pass
else:
    assert value == 1
""".strip()
            ),
            seen_assertions=while_else_duplicate_seen,
            unittest_receiver_name=None,
        )
        is True
    )

    match_duplicate_seen: set[duplicate_assert._AssertionKey] = {bare_key}
    assert (
        duplicate_assert._statement_has_duplicate_assertion(
            _statement(
                """
match value:
    case candidate if candidate > 0:
        assert value == 1
""".strip()
            ),
            seen_assertions=match_duplicate_seen,
            unittest_receiver_name=None,
        )
        is True
    )


def test_statement_duplicate_assertion_handles_try_handlers_finally_and_handler_state() -> None:
    bare_key = _bare_assert_key("value == 1")
    unittest_key = _unittest_key("self.assertEqual(value, 1)")
    handler_type = ast.Call(
        func=ast.Attribute(
            value=ast.Name(id="self", ctx=ast.Load()),
            attr="assertEqual",
            ctx=ast.Load(),
        ),
        args=[
            ast.Name(id="value", ctx=ast.Load()),
            ast.Constant(1),
        ],
        keywords=[],
    )

    handler_type_seen: set[duplicate_assert._AssertionKey] = {unittest_key}
    assert (
        duplicate_assert._statement_has_duplicate_assertion(
            ast.Try(
                body=[ast.Pass()],
                handlers=[
                    ast.ExceptHandler(type=handler_type, name=None, body=[ast.Pass()])
                ],
                orelse=[],
                finalbody=[],
            ),
            seen_assertions=handler_type_seen,
            unittest_receiver_name="self",
        )
        is True
    )

    try_body_duplicate_seen: set[duplicate_assert._AssertionKey] = {bare_key}
    assert (
        duplicate_assert._statement_has_duplicate_assertion(
            _statement(
                """
try:
    assert value == 1
except RuntimeError:
    pass
""".strip()
            ),
            seen_assertions=try_body_duplicate_seen,
            unittest_receiver_name=None,
        )
        is True
    )

    try_orelse_duplicate_seen: set[duplicate_assert._AssertionKey] = {bare_key}
    assert (
        duplicate_assert._statement_has_duplicate_assertion(
            _statement(
                """
try:
    pass
except RuntimeError:
    pass
else:
    assert value == 1
""".strip()
            ),
            seen_assertions=try_orelse_duplicate_seen,
            unittest_receiver_name=None,
        )
        is True
    )

    finalbody_duplicate_seen: set[duplicate_assert._AssertionKey] = set()
    assert (
        duplicate_assert._statement_has_duplicate_assertion(
            _statement(
                """
try:
    assert value == 1
except RuntimeError:
    assert value == 1
finally:
    assert value == 1
""".strip()
            ),
            seen_assertions=finalbody_duplicate_seen,
            unittest_receiver_name=None,
        )
        is True
    )

    no_finalbody_seen: set[duplicate_assert._AssertionKey] = set()
    assert (
        duplicate_assert._statement_has_duplicate_assertion(
            _statement(
                """
try:
    assert value == 1
except RuntimeError:
    pass
""".strip()
            ),
            seen_assertions=no_finalbody_seen,
            unittest_receiver_name=None,
        )
        is False
    )
    assert no_finalbody_seen == set()

    handler_entry_seen = duplicate_assert._collect_try_handler_entry_seen(
        [
            _statement("assert value == 1"),
            _statement("self.assertEqual(value, 1)"),
            _statement("pass"),
            _statement('"docstring"'),
            _statement("raise RuntimeError()"),
        ],
        seen_assertions=set(),
        unittest_receiver_name="self",
    )
    reset_seen = duplicate_assert._collect_try_handler_entry_seen(
        [
            _statement("assert value == 1"),
            _statement("result = transform(value)"),
        ],
        seen_assertions=set(),
        unittest_receiver_name=None,
    )

    assert handler_entry_seen == {bare_key, unittest_key}
    assert reset_seen == set()


def test_statement_header_and_normalization_helpers_cover_remaining_statement_forms() -> None:
    ann_assign = _function_statement("value: int = self.assertEqual(result, 1)")
    aug_assign = _function_statement("total += self.assertEqual(result, 1)")
    return_statement = _function_statement("return self.assertEqual(result, 1)")
    raise_statement = _function_statement("raise self.assertEqual(result, 1) from self.fail()")
    with_statement = _function_statement("with self.assertEqual(result, 1):\n    pass")
    match_statement = _function_statement(
        "match self.assertEqual(result, 1):\n    case _:\n        pass"
    )
    match_guard = _function_statement(
        "match result:\n    case _ if self.assertEqual(result, 1):\n        pass"
    )

    assert len(duplicate_assert._iter_statement_header_expressions(ann_assign)) == 1
    assert len(duplicate_assert._iter_statement_header_expressions(aug_assign)) == 1
    assert len(duplicate_assert._iter_statement_header_expressions(return_statement)) == 1
    assert len(duplicate_assert._iter_statement_header_expressions(raise_statement)) == 2
    assert len(duplicate_assert._iter_statement_header_expressions(with_statement)) == 1
    assert len(duplicate_assert._iter_statement_header_expressions(match_statement)) == 1
    assert (
        duplicate_assert._record_expression_assertions(
            _expression("(lambda: self.assertEqual(result, 1))"),
            seen_assertions=set(),
            unittest_receiver_name="self",
        )
        is False
    )
    assert (
        duplicate_assert._statement_has_duplicate_assertion(
            match_guard,
            seen_assertions={_unittest_key("self.assertEqual(result, 1)")},
            unittest_receiver_name="self",
        )
        is True
    )
    assert duplicate_assert._intersect_seen_assertions([]) == set()
    assert duplicate_assert._normalize_ast([1, (2, 3)])
    assert duplicate_assert._normalize_unittest_assertion_call(
        _expression("assertEqual(result, 1)"),
        receiver_name="self",
    ) is None
    assert duplicate_assert._normalize_unittest_assertion_call(
        _expression("other.assertEqual(result, 1)"),
        receiver_name="self",
    ) is None
    assert duplicate_assert._normalize_unittest_assertion_call(
        _expression("self.helper(result, 1)"),
        receiver_name="self",
    ) is None


def test_control_flow_helpers_recognize_fallthrough_triviality_and_match_exhaustiveness() -> None:
    static_false_if = _statement(
        """
if False:
    return
else:
    pass
""".strip()
    )
    try_without_finally = _statement(
        """
try:
    return
except RuntimeError:
    pass
""".strip()
    )
    try_with_non_fallthrough_finally = _statement(
        """
try:
    pass
except RuntimeError:
    return
finally:
    return
""".strip()
    )
    catch_all_match = _statement(
        """
match value:
    case _:
        pass
""".strip()
    )

    assert duplicate_assert._statement_can_fall_through(static_false_if) is True
    assert duplicate_assert._statement_can_fall_through(try_without_finally) is True
    assert duplicate_assert._statement_can_fall_through(try_with_non_fallthrough_finally) is False
    assert (
        duplicate_assert._try_pre_finally_can_fall_through(try_with_non_fallthrough_finally)
        is True
    )
    assert duplicate_assert._extract_top_level_unittest_assertion_key(
        _statement("value = 1"),
        unittest_receiver_name="self",
    ) is None
    assert duplicate_assert._extract_top_level_unittest_assertion_key(
        _statement("result"),
        unittest_receiver_name="self",
    ) is None
    assert duplicate_assert._is_trivial_statement(_statement("pass")) is True
    assert duplicate_assert._is_trivial_statement(_statement('"docstring"')) is True
    assert duplicate_assert._has_match_catch_all(catch_all_match) is True


def _statement(source: str) -> ast.stmt:
    return ast.parse(source, mode="exec").body[0]


def _function_statement(source: str) -> ast.stmt:
    body = textwrap.indent(source, "    ")
    function = ast.parse(
        f"def test_example(self, result, total):\n{body}",
        mode="exec",
    ).body[0]
    return function.body[0]


def _expression(source: str) -> ast.expr:
    return ast.parse(source, mode="eval").body


def _bare_assert_key(source: str) -> duplicate_assert._AssertionKey:
    return duplicate_assert._normalize_bare_assert(_statement(f"assert {source}"))


def _unittest_key(source: str) -> duplicate_assert._AssertionKey:
    expression = _expression(source)
    assert isinstance(expression, ast.Call)
    key = duplicate_assert._normalize_unittest_assertion_call(expression, receiver_name="self")
    assert key is not None
    return key
