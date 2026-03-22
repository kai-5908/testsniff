from __future__ import annotations

from pathlib import Path

from testsniff.parser.loader import load_source
from testsniff.parser.module_context import ModuleContext
from testsniff.reporting.finding import Finding
from testsniff.rules.checks.disabled_ignored_test import DisabledIgnoredTestRule

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "disabled_ignored_test"


def test_disabled_ignored_rule_reports_pytest_skip_decorator() -> None:
    findings = _analyze_fixture("positive_pytest_skip.py")

    assert len(findings) == 1
    finding = findings[0]
    assert finding.rule_id == "TS004"
    assert finding.severity == "warning"
    assert finding.confidence == "high"
    assert finding.line == 5


def test_disabled_ignored_rule_reports_pytest_skipif_module_alias() -> None:
    findings = _analyze_fixture("positive_pytest_skipif_alias.py")

    assert len(findings) == 1
    assert findings[0].rule_id == "TS004"
    assert findings[0].line == 5


def test_disabled_ignored_rule_reports_unittest_skip_direct_import_alias() -> None:
    findings = _analyze_fixture("positive_unittest_skip_import_alias.py")

    assert len(findings) == 1
    assert findings[0].rule_id == "TS004"
    assert findings[0].line == 7


def test_disabled_ignored_rule_reports_unittest_skipif_case_module_alias() -> None:
    findings = _analyze_fixture("positive_unittest_skipif_case_module.py")

    assert len(findings) == 1
    assert findings[0].rule_id == "TS004"
    assert findings[0].line == 7


def test_disabled_ignored_rule_reports_unittest_skipunless_module_alias() -> None:
    findings = _analyze_fixture("positive_unittest_skipunless_module_alias.py")

    assert len(findings) == 1
    assert findings[0].rule_id == "TS004"
    assert findings[0].line == 6


def test_disabled_ignored_rule_expands_class_level_pytest_skip_to_each_method() -> None:
    findings = _analyze_fixture("positive_class_level_pytest_skip.py")

    assert len(findings) == 2
    assert [finding.line for finding in findings] == [6, 9]
    assert all(finding.rule_id == "TS004" for finding in findings)
    assert all(finding.headline == findings[0].headline for finding in findings)
    assert all(finding.why == findings[0].why for finding in findings)
    assert all(finding.fix == findings[0].fix for finding in findings)


def test_disabled_ignored_rule_ignores_pytest_mark_direct_import() -> None:
    findings = _analyze_fixture("negative_pytest_mark_direct_import.py")

    assert findings == []


def test_disabled_ignored_rule_ignores_pytest_mark_direct_import_alias() -> None:
    findings = _analyze_source(
        """
from pytest import mark as pt_mark

@pt_mark.skip(reason="temporarily disabled")
def test_example():
    assert True
""".strip()
    )

    assert findings == []


def test_disabled_ignored_rule_ignores_expected_failure() -> None:
    findings = _analyze_fixture("negative_expected_failure.py")

    assert findings == []


def test_disabled_ignored_rule_ignores_runtime_pytest_skip_calls() -> None:
    findings = _analyze_fixture("negative_runtime_pytest_skip.py")

    assert findings == []


def test_disabled_ignored_rule_ignores_pytest_skipif_with_static_false_condition() -> None:
    findings = _analyze_source(
        """
import pytest

@pytest.mark.skipif(False, reason="temporarily disabled")
def test_example():
    assert True
""".strip()
    )

    assert findings == []


def test_disabled_ignored_rule_ignores_pytest_skipif_with_static_falsy_constant() -> None:
    findings = _analyze_source(
        """
import pytest

@pytest.mark.skipif(0, reason="temporarily disabled")
def test_example():
    assert True
""".strip()
    )

    assert findings == []


def test_disabled_ignored_rule_ignores_pytest_skipif_with_static_none_condition() -> None:
    findings = _analyze_source(
        """
import pytest

@pytest.mark.skipif(None, reason="temporarily disabled")
def test_example():
    assert True
""".strip()
    )

    assert findings == []


def test_disabled_ignored_rule_ignores_pytest_skipif_with_condition_keyword() -> None:
    findings = _analyze_source(
        """
import pytest

@pytest.mark.skipif(condition="", reason="temporarily disabled")
def test_example():
    assert True
""".strip()
    )

    assert findings == []


def test_disabled_ignored_rule_ignores_unittest_skipif_with_static_false_condition() -> None:
    findings = _analyze_source(
        """
import unittest

class TestExample(unittest.TestCase):
    @unittest.skipIf(False, "temporarily disabled")
    def test_example(self):
        self.assertTrue(True)
""".strip()
    )

    assert findings == []


def test_disabled_ignored_rule_ignores_unittest_skipif_with_static_falsy_constant() -> None:
    findings = _analyze_source(
        """
import unittest

class TestExample(unittest.TestCase):
    @unittest.skipIf(0, "temporarily disabled")
    def test_example(self):
        self.assertTrue(True)
""".strip()
    )

    assert findings == []


def test_disabled_ignored_rule_ignores_unittest_skipif_with_condition_keyword() -> None:
    findings = _analyze_source(
        """
import unittest

class TestExample(unittest.TestCase):
    @unittest.skipIf(condition=False, reason="temporarily disabled")
    def test_example(self):
        self.assertTrue(True)
""".strip()
    )

    assert findings == []


def test_disabled_ignored_rule_ignores_unittest_skipunless_with_static_true_condition() -> None:
    findings = _analyze_source(
        """
import unittest

class TestExample(unittest.TestCase):
    @unittest.skipUnless(True, "temporarily disabled")
    def test_example(self):
        self.assertTrue(True)
""".strip()
    )

    assert findings == []


def test_disabled_ignored_rule_ignores_unittest_skipunless_with_static_truthy_constant() -> None:
    findings = _analyze_source(
        """
import unittest

class TestExample(unittest.TestCase):
    @unittest.skipUnless(1, "temporarily disabled")
    def test_example(self):
        self.assertTrue(True)
""".strip()
    )

    assert findings == []


def test_disabled_ignored_rule_ignores_unittest_skipunless_with_condition_keyword() -> None:
    findings = _analyze_source(
        """
import unittest

class TestExample(unittest.TestCase):
    @unittest.skipUnless(condition=True, reason="temporarily disabled")
    def test_example(self):
        self.assertTrue(True)
""".strip()
    )

    assert findings == []



def test_disabled_ignored_rule_ignores_unrelated_decorators() -> None:
    findings = _analyze_fixture("negative_unrelated_decorator.py")

    assert findings == []


def test_disabled_ignored_rule_recognizes_imports_from_static_truthy_if_block() -> None:
    findings = _analyze_source(
        """
if True:
    import pytest as pt

@pt.mark.skip(reason="temporarily disabled")
def test_example():
    assert True
""".strip()
    )

    assert len(findings) == 1
    assert findings[0].rule_id == "TS004"


def test_disabled_ignored_rule_drops_shadowed_alias_from_static_truthy_if_block() -> None:
    findings = _analyze_source(
        """
import pytest

def helper():
    return None

if True:
    pytest = helper

@pytest.mark.skip(reason="temporarily disabled")
def test_example():
    assert True
""".strip()
    )

    assert findings == []


def test_disabled_ignored_rule_drops_shadowed_alias_from_unknown_if_branch() -> None:
    findings = _analyze_source(
        """
import pytest

flag = object()

def helper():
    return None

if flag:
    pytest = helper

@pytest.mark.skip(reason="temporarily disabled")
def test_example():
    assert True
""".strip()
    )

    assert findings == []


def test_disabled_ignored_rule_drops_alias_from_if_condition_named_expression() -> None:
    findings = _analyze_source(
        """
import pytest

if (pytest := object()):
    pass

@pytest.mark.skip(reason="temporarily disabled")
def test_example():
    assert True
""".strip()
    )

    assert findings == []


def test_disabled_ignored_rule_drops_shadowed_alias_from_try_block() -> None:
    findings = _analyze_source(
        """
import pytest

def helper():
    return None

try:
    pytest = helper
finally:
    pass

@pytest.mark.skip(reason="temporarily disabled")
def test_example():
    assert True
""".strip()
    )

    assert findings == []


def test_disabled_ignored_rule_drops_alias_from_while_condition_named_expression() -> None:
    findings = _analyze_source(
        """
import pytest

while (pytest := None):
    pass

@pytest.mark.skip(reason="temporarily disabled")
def test_example():
    assert True
""".strip()
    )

    assert findings == []


def test_disabled_ignored_rule_drops_shadowed_alias_from_match_capture() -> None:
    findings = _analyze_source(
        """
import pytest

match object():
    case pytest:
        pass

@pytest.mark.skip(reason="temporarily disabled")
def test_example():
    assert True
""".strip()
    )

    assert findings == []


def test_disabled_ignored_rule_drops_alias_from_match_subject_named_expression() -> None:
    findings = _analyze_source(
        """
import pytest

match (pytest := object()):
    case _:
        pass

@pytest.mark.skip(reason="temporarily disabled")
def test_example():
    assert True
""".strip()
    )

    assert findings == []


def test_disabled_ignored_rule_drops_alias_after_delete() -> None:
    findings = _analyze_source(
        """
import pytest

del pytest

@pytest.mark.skip(reason="temporarily disabled")
def test_example():
    assert True
""".strip()
    )

    assert findings == []


def test_disabled_ignored_rule_drops_alias_after_named_expression_rebinding() -> None:
    findings = _analyze_source(
        """
import pytest

(pytest := object())

@pytest.mark.skip(reason="temporarily disabled")
def test_example():
    assert True
""".strip()
    )

    assert findings == []


def test_disabled_ignored_rule_keeps_duplicate_test_class_names_distinct() -> None:
    findings = _analyze_source(
        """
import pytest

@pytest.mark.skip(reason="temporarily disabled")
class TestExample:
    def test_first(self):
        assert True

class TestExample:
    def test_second(self):
        assert True
""".strip()
    )

    assert len(findings) == 1
    assert findings[0].line == 5


def test_disabled_ignored_rule_handles_many_unique_import_aliases() -> None:
    import_lines = [f"import unittest as u{index}" for index in range(2000)]
    source = "\n".join(
        [
            *import_lines,
            "",
            "@u1999.skipIf(True, 'temporarily disabled')",
            "def test_example():",
            "    assert True",
        ]
    )

    findings = _analyze_source(source)

    assert len(findings) == 1
    assert findings[0].rule_id == "TS004"


def _analyze_fixture(filename: str) -> list[Finding]:
    path = FIXTURES_DIR / filename
    module = ModuleContext.from_source(path, load_source(path))
    return DisabledIgnoredTestRule().analyze(module)


def _analyze_source(source: str) -> list[Finding]:
    module = ModuleContext.from_source(Path("tests/test_inline_disabled_ignored.py"), source)
    return DisabledIgnoredTestRule().analyze(module)
