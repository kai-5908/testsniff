from __future__ import annotations

import ast
from pathlib import Path

import testsniff.rules.checks.missing_assertion as missing_assertion
from testsniff.parser.module_context import ModuleContext
from testsniff.rules.checks.missing_assertion import MissingAssertionRule


def test_collect_pytest_aliases_handles_non_module_trees_and_parameter_shadowing() -> None:
    aliases = missing_assertion._collect_pytest_aliases(ast.parse("value", mode="eval"))
    function = ast.parse(
        """
def test_example(arg, /, value, *args, kwonly, **kwargs):
    pass
""".strip(),
        mode="exec",
    ).body[0]

    assert aliases == missing_assertion._PytestAliasSet(
        module_aliases=frozenset(),
        helper_names=frozenset(),
    )
    assert missing_assertion._collect_parameter_names(function) == {
        "arg",
        "value",
        "args",
        "kwonly",
        "kwargs",
    }


def test_import_statement_updates_pytest_module_aliases_inside_a_test() -> None:
    pytest_aliases = _target_aliases()
    statement = _statement("import pytest as pt")

    recognized = missing_assertion._statement_has_recognized_assertion(
        statement,
        unittest_receiver_name=None,
        pytest_aliases=pytest_aliases,
    )

    assert recognized is False
    assert pytest_aliases.module_aliases == {"pt"}


def test_with_and_for_blocks_recognize_meaningful_assertions_in_executable_paths() -> None:
    pytest_aliases = _target_aliases()

    with_statement = _statement(
        """
with manager():
    assert response.status_code == 200
"""
    )
    for_body_statement = _statement(
        """
for response in responses:
    assert response.ok
"""
    )
    for_else_statement = _statement(
        """
for response in responses:
    pass
else:
    assert fallback.ok
"""
    )

    assert _has_assertion(with_statement, pytest_aliases=pytest_aliases) is True
    assert _has_assertion(for_body_statement, pytest_aliases=_target_aliases()) is True
    assert _has_assertion(for_else_statement, pytest_aliases=_target_aliases()) is True


def test_try_statement_recognizes_assertions_in_body_else_handler_type_and_handler_body() -> None:
    body_statement = _statement(
        """
try:
    assert result.ok
except RuntimeError:
    pass
"""
    )
    else_statement = _statement(
        """
try:
    pass
except RuntimeError:
    pass
else:
    assert result.ok
"""
    )
    handler_body_statement = _statement(
        """
try:
    pass
except RuntimeError:
    assert error is not None
"""
    )
    handler_type_statement = ast.Try(
        body=[ast.Pass()],
        handlers=[
            ast.ExceptHandler(
                type=ast.Call(
                    func=ast.Attribute(
                        value=ast.Name(id="pytest", ctx=ast.Load()),
                        attr="fail",
                        ctx=ast.Load(),
                    ),
                    args=[],
                    keywords=[],
                ),
                name=None,
                body=[ast.Pass()],
            )
        ],
        orelse=[],
        finalbody=[],
    )

    assert _has_assertion(body_statement, pytest_aliases=_target_aliases()) is True
    assert _has_assertion(else_statement, pytest_aliases=_target_aliases()) is True
    assert _has_assertion(handler_body_statement, pytest_aliases=_target_aliases()) is True
    assert _has_assertion(
        handler_type_statement,
        pytest_aliases=_target_aliases(module_aliases=("pytest",)),
    ) is True


def test_if_statement_handles_else_assertions_and_alias_propagation() -> None:
    else_assertion_statement = _statement(
        """
if condition:
    pass
else:
    assert result.ok
"""
    )
    truthy_import_statement = _statement(
        """
if True:
    import pytest as pt
else:
    import pytest as other
"""
    )
    falsy_import_statement = _statement(
        """
if False:
    import pytest as unused
else:
    import pytest as py
"""
    )
    unknown_import_statement = _statement(
        """
if condition:
    import pytest as shared
else:
    import pytest as shared
"""
    )

    truthy_aliases = _target_aliases()
    falsy_aliases = _target_aliases()
    unknown_aliases = _target_aliases()

    assert _has_assertion(else_assertion_statement, pytest_aliases=_target_aliases()) is True
    assert _has_assertion(truthy_import_statement, pytest_aliases=truthy_aliases) is False
    assert _has_assertion(falsy_import_statement, pytest_aliases=falsy_aliases) is False
    assert _has_assertion(unknown_import_statement, pytest_aliases=unknown_aliases) is False
    assert truthy_aliases.module_aliases == {"pt"}
    assert falsy_aliases.module_aliases == {"py"}
    assert unknown_aliases.module_aliases == {"shared"}


def test_while_statement_handles_body_else_and_alias_propagation() -> None:
    body_assertion_statement = _statement(
        """
while condition:
    assert result.ok
"""
    )
    else_assertion_statement = _statement(
        """
while condition:
    pass
else:
    assert fallback.ok
"""
    )
    falsy_import_statement = _statement(
        """
while False:
    import pytest as unused
else:
    import pytest as py
"""
    )
    unknown_import_statement = _statement(
        """
while condition:
    import pytest as shared
else:
    import pytest as shared
"""
    )

    falsy_aliases = _target_aliases()
    unknown_aliases = _target_aliases()

    assert _has_assertion(body_assertion_statement, pytest_aliases=_target_aliases()) is True
    assert _has_assertion(else_assertion_statement, pytest_aliases=_target_aliases()) is True
    assert _has_assertion(falsy_import_statement, pytest_aliases=falsy_aliases) is False
    assert _has_assertion(unknown_import_statement, pytest_aliases=unknown_aliases) is False
    assert falsy_aliases.module_aliases == {"py"}
    assert unknown_aliases.module_aliases == {"shared"}


def test_match_statement_handles_guard_body_and_shared_aliases() -> None:
    guard_statement = _statement(
        """
match response:
    case _ if pytest.fail():
        pass
"""
    )
    body_statement = _statement(
        """
match response:
    case _:
        assert response.ok
"""
    )
    alias_statement = _statement(
        """
match response:
    case 200:
        import pytest as pt
    case _:
        import pytest as pt
"""
    )

    alias_state = _target_aliases()

    assert _has_assertion(
        guard_statement,
        pytest_aliases=_target_aliases(module_aliases=("pytest",)),
    ) is True
    assert _has_assertion(body_statement, pytest_aliases=_target_aliases()) is True
    assert _has_assertion(alias_statement, pytest_aliases=alias_state) is False
    assert alias_state.module_aliases == {"pt"}


def test_pattern_capture_name_collection_handles_nested_match_shapes() -> None:
    nested_pattern = _statement(
        """
match value:
    case {
        "key": [first, *rest],
        "other": Point(positional, x=coord) | [alt],
        **mapping_rest,
    } as whole:
        pass
"""
    ).cases[0].pattern
    value_pattern = _statement(
        """
match value:
    case 0:
        pass
"""
    ).cases[0].pattern

    assert missing_assertion._collect_pattern_capture_names(nested_pattern) == {
        "alt",
        "coord",
        "first",
        "mapping_rest",
        "positional",
        "rest",
        "whole",
    }
    assert missing_assertion._collect_pattern_capture_names(value_pattern) == set()


def test_statement_header_helpers_cover_annotations_augassign_returns_and_raise_causes() -> None:
    ann_assign = _statement("value: int")
    ann_assign_with_value = _statement("value: int = pytest.fail()")
    aug_assign = _statement("counter += pytest.fail()")
    return_statement = ast.Return(value=None)
    return_with_value = ast.Return(value=ast.Name(id="result", ctx=ast.Load()))
    raise_statement = _statement("raise RuntimeError() from pytest.fail()")

    assert missing_assertion._iter_statement_header_expressions(ann_assign) == ()
    assert missing_assertion._iter_statement_header_expressions(ann_assign_with_value) == (
        ann_assign_with_value.value,
    )
    assert missing_assertion._statement_header_has_recognized_assertion(
        aug_assign,
        unittest_receiver_name=None,
        pytest_aliases=_target_aliases(module_aliases=("pytest",)),
    )
    assert missing_assertion._iter_statement_header_expressions(return_statement) == ()
    assert missing_assertion._iter_statement_header_expressions(return_with_value) == (
        return_with_value.value,
    )
    assert missing_assertion._statement_header_has_recognized_assertion(
        raise_statement,
        unittest_receiver_name=None,
        pytest_aliases=_target_aliases(module_aliases=("pytest",)),
    )


def test_lambda_wrapped_pytest_calls_do_not_count_as_real_assertions() -> None:
    module = ModuleContext.from_source(
        Path("tests/test_lambda_missing_assertion.py"),
        """
import pytest

def test_example():
    callback = lambda: pytest.fail()
    callback
""".strip(),
    )

    findings = MissingAssertionRule().analyze(module)

    assert len(findings) == 1
    assert findings[0].rule_id == "TS003"


def test_rebound_name_collection_covers_for_with_except_and_starred_targets() -> None:
    ann_assign = _statement("value: int")
    for_statement = _statement(
        """
for helper in helpers:
    pass
"""
    )
    with_statement = _statement(
        """
with manager() as (left, *rest):
    pass
"""
    )
    except_handler = ast.ExceptHandler(
        type=ast.Name(id="Exception", ctx=ast.Load()),
        name="err",
        body=[],
    )

    assert missing_assertion._collect_rebound_names(ann_assign) == {"value"}
    assert missing_assertion._collect_rebound_names(for_statement) == {"helper"}
    assert missing_assertion._collect_rebound_names(with_statement) == {"left", "rest"}
    assert missing_assertion._collect_rebound_names(except_handler) == {"err"}
    assert missing_assertion._collect_target_names(
        ast.Tuple(
            elts=[
                ast.Name(id="first", ctx=ast.Store()),
                ast.Starred(value=ast.Name(id="rest", ctx=ast.Store()), ctx=ast.Store()),
            ],
            ctx=ast.Store(),
        )
    ) == {"first", "rest"}
    assert missing_assertion._collect_target_names(ast.Constant(value=1)) == set()


def test_assertion_call_detection_requires_matching_receivers_and_supported_call_shapes() -> None:
    wrong_receiver_call = ast.parse("other.assertEqual(1, 1)", mode="eval").body
    dynamic_attribute_call = ast.parse("factory().raises(ValueError)", mode="eval").body
    unsupported_func_call = ast.parse("get_callable()()", mode="eval").body

    assert (
        missing_assertion._is_unittest_assertion_call(wrong_receiver_call, receiver_name="self")
        is False
    )
    assert (
        missing_assertion._is_pytest_assertion_call(
            dynamic_attribute_call,
            _target_aliases(module_aliases=("pytest",)),
        )
        is False
    )
    assert (
        missing_assertion._is_pytest_assertion_call(
            unsupported_func_call,
            _target_aliases(helper_names=("raises",)),
        )
        is False
    )


def _statement(source: str) -> ast.stmt:
    return ast.parse(source, mode="exec").body[0]


def _target_aliases(
    *,
    module_aliases: tuple[str, ...] = (),
    helper_names: tuple[str, ...] = (),
) -> missing_assertion._TargetPytestAliases:
    return missing_assertion._TargetPytestAliases(
        module_aliases=set(module_aliases),
        helper_names=set(helper_names),
    )


def _has_assertion(
    statement: ast.stmt,
    *,
    pytest_aliases: missing_assertion._TargetPytestAliases,
) -> bool:
    return missing_assertion._statement_has_recognized_assertion(
        statement,
        unittest_receiver_name=None,
        pytest_aliases=pytest_aliases,
    )
