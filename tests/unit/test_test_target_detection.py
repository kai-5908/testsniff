from __future__ import annotations

from pathlib import Path

from testsniff.parser import ast_index
from testsniff.parser.module_context import ModuleContext


def test_detects_pytest_targets_and_excludes_nested_and_class_helpers() -> None:
    module = ModuleContext.from_source(
        Path("tests/test_targets.py"),
        """
def helper():
    pass

def test_top_level():
    pass

async def test_async_top_level():
    pass

def outer():
    def test_nested():
        pass

class PlainClass:
    def test_method(self):
        pass
""".strip(),
    )

    assert _summarize(module) == [
        ("pytest", None, "test_top_level"),
        ("pytest", None, "test_async_top_level"),
    ]


def test_detects_unittest_targets_from_direct_and_indirect_inheritance() -> None:
    module = ModuleContext.from_source(
        Path("tests/test_unittest_targets.py"),
        """
from unittest import TestCase as BaseCase
import unittest as ut

class Direct(BaseCase):
    def helper(self):
        pass

    def test_direct(self):
        pass

class Indirect(Direct):
    async def test_indirect(self):
        pass

class Namespaced(ut.TestCase):
    def test_namespaced(self):
        pass

class Plain:
    def test_not_a_target(self):
        pass
""".strip(),
    )

    assert _summarize(module) == [
        ("unittest", "Direct", "test_direct"),
        ("unittest", "Indirect", "test_indirect"),
        ("unittest", "Namespaced", "test_namespaced"),
    ]


def test_does_not_treat_non_unittest_testcase_names_as_targets() -> None:
    module = ModuleContext.from_source(
        Path("tests/test_custom_testcase.py"),
        """
class TestCase:
    pass

class LooksSimilar(TestCase):
    def test_fake(self):
        pass
""".strip(),
    )

    assert _summarize(module) == []


def test_resolves_reverse_ordered_unittest_inheritance_in_linear_base_resolution(
    monkeypatch,
) -> None:
    class_count = 512
    lines = ["from unittest import TestCase"]

    for index in range(class_count, 0, -1):
        base_name = "TestCase" if index == 1 else f"Case{index - 1}"
        lines.extend(
            [
                f"class Case{index}({base_name}):",
                f"    def test_case_{index}(self):",
                "        pass",
                "",
            ]
        )

    calls = 0
    original = ast_index._resolve_base_reference

    def counted_resolve_base_reference(
        base,
        *,
        unittest_aliases,
        testcase_aliases,
        class_names,
    ):
        nonlocal calls
        calls += 1
        return original(
            base,
            unittest_aliases=unittest_aliases,
            testcase_aliases=testcase_aliases,
            class_names=class_names,
        )

    monkeypatch.setattr(
        ast_index,
        "_resolve_base_reference",
        counted_resolve_base_reference,
    )

    module = ModuleContext.from_source(
        Path("tests/test_reverse_unittest_targets.py"),
        "\n".join(lines),
    )

    assert len(module.index.test_targets) == class_count
    assert calls == class_count
    assert module.index.test_targets[0].class_name == "Case512"
    assert module.index.test_targets[-1].class_name == "Case1"


def _summarize(module: ModuleContext) -> list[tuple[str, str | None, str]]:
    return [
        (target.style, target.class_name, target.node.name)
        for target in module.index.test_targets
    ]
