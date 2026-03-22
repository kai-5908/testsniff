from __future__ import annotations

import ast
from pathlib import Path

import testsniff.rules.checks.disabled_ignored_test as disabled_ignored_test
from testsniff.parser.ast_index import ASTIndex
from testsniff.parser.module_context import ModuleContext
from testsniff.rules.checks.disabled_ignored_test import DisabledIgnoredTestRule


def test_disabled_ignored_rule_handles_non_module_trees_and_dynamic_decorators() -> None:
    tree = ast.parse("value", mode="eval")
    module = ModuleContext(
        path=Path("tests/test_disabled_ignored_eval.py"),
        source_text="value",
        tree=tree,
        tokens=(),
        index=ASTIndex.from_tree(tree, total_lines=1),
    )

    assert DisabledIgnoredTestRule().analyze(module) == []
    assert (
        disabled_ignored_test._decorator_disables_target(
            _expression("factory().skip"),
            disabled_ignored_test._new_alias_state(),
        )
        is False
    )


def test_disabled_ignored_rule_tracks_aliases_across_control_flow_and_avoids_duplicates() -> None:
    with_alias_findings = _analyze_source(
        """
def manager():
    return object()

with manager() as resource:
    import pytest as pt

@pt.mark.skip(reason="temporarily disabled")
def test_with_alias():
    assert True
""".strip()
    )
    static_false_if_findings = _analyze_source(
        """
if False:
    import pytest as unused
else:
    import pytest as pt

@pt.mark.skip(reason="temporarily disabled")
def test_if_alias():
    assert True
""".strip()
    )
    static_false_while_findings = _analyze_source(
        """
while False:
    import pytest as unused
else:
    import pytest as pt

@pt.mark.skip(reason="temporarily disabled")
def test_while_alias():
    assert True
""".strip()
    )
    loop_shadow_findings = _analyze_source(
        """
import pytest

for pytest in [object()]:
    pass
else:
    pass

@pytest.mark.skip(reason="temporarily disabled")
def test_loop_shadow():
    assert True
""".strip()
    )
    try_shadow_findings = _analyze_source(
        """
import pytest

try:
    pass
except RuntimeError as pytest:
    pass
finally:
    pass

@pytest.mark.skip(reason="temporarily disabled")
def test_try_shadow():
    assert True
""".strip()
    )
    duplicate_decorator_findings = _analyze_source(
        """
import pytest

@pytest.mark.skip(reason="temporarily disabled")
class TestExample:
    @pytest.mark.skip(reason="temporarily disabled")
    def test_once(self):
        assert True
""".strip()
    )

    assert [finding.line for finding in with_alias_findings] == [8]
    assert [finding.line for finding in static_false_if_findings] == [7]
    assert [finding.line for finding in static_false_while_findings] == [7]
    assert loop_shadow_findings == []
    assert try_shadow_findings == []
    assert [finding.line for finding in duplicate_decorator_findings] == [6]


def test_disabled_ignored_rule_is_conservative_for_dynamic_skip_conditions() -> None:
    alias_state = disabled_ignored_test._new_alias_state()
    alias_state.pytest_module_aliases.add("pytest")
    alias_state.unittest_skip_names["mystery"] = "mystery"

    assert (
        disabled_ignored_test._decorator_disables_target(
            _expression('pytest.mark.skipif(flag, reason="temporarily disabled")'),
            alias_state,
        )
        is True
    )
    assert disabled_ignored_test._resolve_static_condition_truthiness(
        _expression("pytest.mark.skip")
    ) is None
    assert disabled_ignored_test._resolve_static_condition_truthiness(
        ast.Call(
            func=ast.Name(id="skipif", ctx=ast.Load()),
            args=[],
            keywords=[ast.keyword(arg="reason", value=ast.Constant("later"))],
        )
    ) is None
    assert (
        disabled_ignored_test._decorator_disables_target(
            ast.Name(id="mystery", ctx=ast.Load()),
            alias_state,
        )
        is False
    )


def test_static_truthiness_and_import_alias_helpers_cover_nested_alias_shapes() -> None:
    alias_state = disabled_ignored_test._new_alias_state()
    disabled_ignored_test._apply_import_alias_updates(
        _statement("import unittest.case"),
        alias_state,
    )
    disabled_ignored_test._apply_import_alias_updates(
        _statement("import unittest.case as case_mod"),
        alias_state,
    )
    disabled_ignored_test._apply_import_from_alias_updates(
        _statement("from unittest.case import skipIf, skipUnless as skip_unless"),
        alias_state,
    )

    ann_assign = _statement("pytest: object = (alias := object())")
    aug_assign = _statement("pytest += (alias := 1)")
    for_statement = _statement("for (pytest, *rest) in ((1, 2),):\n    pass")
    with_statement = _statement("with (manager := context()) as (pytest, *rest):\n    pass")
    match_statement = _statement(
        """
match (subject := object()):
    case [first, *rest] if (guard := condition()):
        pass
""".strip()
    )
    lambda_named_expr = _expression("(lambda: (pytest := object()))")
    nested_pattern = ast.MatchAs(
        pattern=ast.MatchSequence(
            patterns=[
                ast.MatchAs(name="left"),
                ast.MatchStar(name="rest"),
            ]
        ),
        name="alias",
    )
    mapping_pattern = ast.MatchMapping(
        keys=[ast.Constant("key")],
        patterns=[ast.MatchAs(name="value")],
        rest="extras",
    )
    class_pattern = ast.MatchClass(
        cls=ast.Name(id="Point", ctx=ast.Load()),
        patterns=[ast.MatchAs(name="x_value")],
        kwd_attrs=["meta"],
        kwd_patterns=[mapping_pattern],
    )
    or_pattern = ast.MatchOr(
        patterns=[
            ast.MatchAs(name="same"),
            ast.MatchAs(name="same"),
        ]
    )
    value_pattern = ast.MatchValue(value=ast.Constant(1))
    except_handler = ast.ExceptHandler(
        type=ast.Name(id="RuntimeError", ctx=ast.Load()),
        name="err",
        body=[ast.Pass()],
    )
    if_statement = _statement("if (pytest := object()):\n    pass")
    unsupported_target = ast.Constant(value=1)

    assert alias_state.unittest_module_aliases == {"unittest"}
    assert alias_state.unittest_case_aliases == {"case_mod"}
    assert alias_state.unittest_skip_names == {
        "skipIf": "skipIf",
        "skip_unless": "skipUnless",
    }
    assert disabled_ignored_test._is_static_literal(_expression("-1")) is True
    assert disabled_ignored_test._is_static_literal(_expression("[1, 2]")) is True
    assert disabled_ignored_test._is_static_literal(_expression('{"key": 1}')) is True
    assert disabled_ignored_test._static_truthiness(_expression("{1}")) is True
    assert disabled_ignored_test._static_truthiness(_expression("{value}")) is None
    assert disabled_ignored_test._static_truthiness(_expression('{"key": 1}')) is True
    assert disabled_ignored_test._static_truthiness(_expression('{"key": value}')) is None
    assert disabled_ignored_test._static_truthiness(_expression("~value")) is None
    assert disabled_ignored_test._static_truthiness(_expression('-"disabled"')) is None
    assert disabled_ignored_test._collect_rebound_names(ann_assign) == {"pytest", "alias"}
    assert disabled_ignored_test._collect_rebound_names(aug_assign) == {"pytest", "alias"}
    assert disabled_ignored_test._collect_rebound_names(for_statement) == {"pytest", "rest"}
    assert disabled_ignored_test._collect_rebound_names(with_statement) == {
        "manager",
        "pytest",
        "rest",
    }
    assert disabled_ignored_test._collect_rebound_names(match_statement) == {"subject", "guard"}
    assert disabled_ignored_test._collect_rebound_names(if_statement) == {"pytest"}
    assert disabled_ignored_test._collect_rebound_names(except_handler) == {"err"}
    assert disabled_ignored_test._collect_with_optional_var_names(with_statement) == {
        "pytest",
        "rest",
    }
    assert disabled_ignored_test._collect_target_names(
        ast.Tuple(
            elts=[
                ast.Name(id="left", ctx=ast.Store()),
                ast.Starred(
                    value=ast.Name(id="rest", ctx=ast.Store()),
                    ctx=ast.Store(),
                ),
            ],
            ctx=ast.Store(),
        )
    ) == {"left", "rest"}
    assert disabled_ignored_test._collect_target_names(unsupported_target) == set()
    assert disabled_ignored_test._collect_named_expr_names(lambda_named_expr) == set()
    assert disabled_ignored_test._collect_pattern_capture_names(nested_pattern) == {
        "alias",
        "left",
        "rest",
    }
    assert disabled_ignored_test._collect_pattern_capture_names(class_pattern) == {
        "x_value",
        "value",
        "extras",
    }
    assert disabled_ignored_test._collect_pattern_capture_names(or_pattern) == {"same"}
    assert disabled_ignored_test._collect_pattern_capture_names(value_pattern) == set()


def test_disabled_ignored_rule_match_guards_and_class_reporting_cover_remaining_defensive_paths(
) -> None:
    findings = _analyze_source(
        """
import pytest

match object():
    case _ if (pytest := object()):
        pass

@pytest.mark.skip(reason="temporarily disabled")
def test_match_guard_shadow():
    assert True
""".strip()
    )
    module = ModuleContext.from_source(
        Path("tests/test_disabled_ignored_class_duplicate.py"),
        """
import pytest

@pytest.mark.skip(reason="temporarily disabled")
class TestExample:
    def test_one(self):
        assert True
""".strip(),
    )
    class_node = next(node for node in module.tree.body if isinstance(node, ast.ClassDef))
    target = module.index.test_targets[0]
    findings_for_class: list[object] = []

    disabled_ignored_test._report_class_targets_if_disabled(
        class_node,
        module_path=str(module.path),
        alias_state=disabled_ignored_test._DecoratorAliasState(
            pytest_module_aliases={"pytest"},
            unittest_module_aliases=set(),
            unittest_case_aliases=set(),
            unittest_skip_names={},
        ),
        targets_by_class_node_id={id(class_node): [target]},
        findings=findings_for_class,
        reported_target_ids={id(target.node)},
    )

    assert findings == []
    assert findings_for_class == []


def _analyze_source(source: str) -> list[object]:
    module = ModuleContext.from_source(
        Path("tests/test_inline_disabled_ignored_semantics.py"),
        source,
    )
    return DisabledIgnoredTestRule().analyze(module)


def _statement(source: str) -> ast.stmt:
    return ast.parse(source, mode="exec").body[0]


def _expression(source: str) -> ast.expr:
    return ast.parse(source, mode="eval").body
