from __future__ import annotations

import ast
from pathlib import Path

from testsniff.parser import ast_index
from testsniff.parser.module_context import ModuleContext


def test_detects_unittest_targets_once_in_diamond_inheritance_graph() -> None:
    module = ModuleContext.from_source(
        Path("tests/test_diamond_unittest_targets.py"),
        """
from unittest import TestCase

class Base(TestCase):
    pass

class Left(Base):
    pass

class Right(Base):
    pass

class Leaf(Left, Right):
    def test_leaf(self):
        pass
""".strip(),
    )

    assert [(target.class_name, target.node.name) for target in module.index.test_targets] == [
        ("Leaf", "test_leaf")
    ]


def test_ignores_non_testcase_base_references_while_collecting_targets() -> None:
    module = ModuleContext.from_source(
        Path("tests/test_non_testcase_bases.py"),
        """
class Derived(UnknownBase):
    def test_fake(self):
        pass
""".strip(),
    )

    assert module.index.test_targets == ()


def test_collect_rebound_names_handles_annotation_augassign_asyncfor_with_and_starred_targets(
) -> None:
    ann_assign = ast.parse("alias: object", mode="exec").body[0]
    aug_assign = ast.parse("counter += 1", mode="exec").body[0]
    async_for = ast.parse(
        """
async def consume(items):
    async for alias in items:
        pass
""".strip(),
        mode="exec",
    ).body[0].body[0]
    with_statement = ast.parse(
        """
with manager() as (left, *rest):
    pass
""".strip(),
        mode="exec",
    ).body[0]

    assert ast_index._collect_rebound_names(ann_assign) == {"alias"}
    assert ast_index._collect_rebound_names(aug_assign) == {"counter"}
    assert ast_index._collect_rebound_names(async_for) == {"alias"}
    assert ast_index._collect_rebound_names(with_statement) == {"left", "rest"}


def test_statement_start_line_uses_decorator_line_for_decorated_definitions() -> None:
    decorated_function = ast.parse(
        """
@first
@second
def test_example():
    pass
""".strip(),
        mode="exec",
    ).body[0]

    assert ast_index._statement_start_line(decorated_function) == 1


def test_resolve_base_reference_returns_none_for_unknown_or_dynamic_bases() -> None:
    base_name = ast.parse("UnknownBase", mode="eval").body
    dotted_call = ast.parse("factory().TestCase", mode="eval").body
    unrelated_dotted = ast.parse("pkg.BaseCase", mode="eval").body

    kwargs = {
        "unittest_aliases": {"ut"},
        "unittest_case_aliases": {"case_pkg"},
        "testcase_aliases": {"BaseCase"},
        "class_names": {"KnownBase"},
    }

    assert ast_index._resolve_base_reference(base_name, **kwargs) is None
    assert ast_index._resolve_base_reference(dotted_call, **kwargs) is None
    assert ast_index._resolve_base_reference(unrelated_dotted, **kwargs) is None


def test_pytest_opt_out_requires_simple___test___false_assignment() -> None:
    tuple_assignment_class = ast.parse(
        """
class TestTupleAssigned:
    __test__, marker = (False, False)

    def test_example(self):
        pass
""".strip(),
        mode="exec",
    ).body[0]
    unrelated_assignment_class = ast.parse(
        """
class TestOtherAssignment:
    enabled = False

    def test_example(self):
        pass
""".strip(),
        mode="exec",
    ).body[0]
    real_opt_out_class = ast.parse(
        """
class TestOptOut:
    __test__ = False

    def test_example(self):
        pass
""".strip(),
        mode="exec",
    ).body[0]

    assert ast_index._has_pytest_opt_out(tuple_assignment_class) is False
    assert ast_index._has_pytest_opt_out(unrelated_assignment_class) is False
    assert ast_index._has_pytest_opt_out(real_opt_out_class) is True


def test_collect_rebound_names_and_target_names_ignore_unsupported_nodes() -> None:
    pass_statement = ast.parse("pass", mode="exec").body[0]

    assert ast_index._collect_rebound_names(pass_statement) == set()
    assert ast_index._collect_target_names(ast.Constant(value=1)) == set()
