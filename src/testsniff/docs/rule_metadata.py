from __future__ import annotations

from dataclasses import dataclass

from testsniff.config.types import Confidence, Severity
from testsniff.reporting.finding import ExampleSnippet


@dataclass(slots=True)
class RuleMetadata:
    rule_id: str
    headline: str
    default_severity: Severity
    default_confidence: Confidence
    why: str
    fix: str
    example: ExampleSnippet
    references: tuple[str, ...]


EMPTY_TEST = RuleMetadata(
    rule_id="TS001",
    headline="Test body is empty",
    default_severity="error",
    default_confidence="high",
    why=(
        "Empty tests can pass without validating behavior, which creates false confidence in the "
        "test suite."
    ),
    fix=(
        "Add a real assertion or remove the placeholder test until the intended behavior can be "
        "verified."
    ),
    example=ExampleSnippet(
        bad='def test_user_creation():\n    pass',
        good=(
            'def test_user_creation():\n'
            '    user = create_user("alice")\n'
            '    assert user.name == "alice"'
        ),
    ),
    references=(
        "docs/product-specs/rule-catalog-scope.md",
        "docs/exec-plans/completed/2026-03-15-empty-test-rule.md",
    ),
)

COMMENTS_ONLY_TEST = RuleMetadata(
    rule_id="TS002",
    headline="Test contains only placeholder comments",
    default_severity="error",
    default_confidence="high",
    why=(
        "Tests that contain only comments or documentation can pass without executing any "
        "verification, which hides unfinished coverage behind descriptive text."
    ),
    fix=(
        "Replace placeholder comments with an executable assertion, or remove the test until "
        "the intended behavior can be verified."
    ),
    example=ExampleSnippet(
        bad=(
            "def test_user_creation():\n"
            '    """TODO: cover the success path."""\n'
            "    # Assert the created user is persisted.\n"
        ),
        good=(
            "def test_user_creation():\n"
            '    user = create_user("alice")\n'
            '    assert user.name == "alice"'
        ),
    ),
    references=(
        "docs/product-specs/rule-catalog-scope.md",
        "docs/exec-plans/completed/2026-03-20-ts002-comments-only-test.md",
    ),
)

MISSING_ASSERTION = RuleMetadata(
    rule_id="TS003",
    headline="Test has no recognized assertion",
    default_severity="error",
    default_confidence="high",
    why=(
        "Tests without a recognized assertion signal can pass without validating behavior, "
        "which creates false confidence in the suite."
    ),
    fix=(
        "Add an explicit assertion such as `assert`, a `self.assert*` call, or an accepted "
        "`pytest` assertion helper like `pytest.raises(...)`."
    ),
    example=ExampleSnippet(
        bad=(
            "def test_user_creation(client):\n"
            '    client.post("/users", json={"name": "alice"})'
        ),
        good=(
            "def test_user_creation(client):\n"
            '    response = client.post("/users", json={"name": "alice"})\n'
            "    assert response.status_code == 201"
        ),
    ),
    references=(
        "docs/product-specs/rule-catalog-scope.md",
        "docs/exec-plans/completed/2026-03-20-ts003-missing-assertion.md",
    ),
)

DISABLED_IGNORED_TEST = RuleMetadata(
    rule_id="TS004",
    headline="Test is disabled or ignored",
    default_severity="warning",
    default_confidence="high",
    why=(
        "Disabled tests reduce suite observability and can hide unverified behavior behind "
        "code that no longer runs in normal test execution."
    ),
    fix=(
        "Re-enable the test, narrow the skip to the few cases that truly require it, or "
        "remove the test until it can run normally."
    ),
    example=ExampleSnippet(
        bad=(
            "import pytest\n\n"
            '@pytest.mark.skip(reason="temporarily disabled")\n'
            "def test_user_creation():\n"
            "    assert create_user(\"alice\").name == \"alice\""
        ),
        good=(
            "import pytest\n\n"
            "def test_user_creation():\n"
            "    assert create_user(\"alice\").name == \"alice\""
        ),
    ),
    references=(
        "docs/product-specs/rule-catalog-scope.md",
        "docs/exec-plans/completed/2026-03-22-ts004-disabled-ignored-test.md",
    ),
)

RULE_METADATA_BY_ID: dict[str, RuleMetadata] = {
    EMPTY_TEST.rule_id: EMPTY_TEST,
    COMMENTS_ONLY_TEST.rule_id: COMMENTS_ONLY_TEST,
    MISSING_ASSERTION.rule_id: MISSING_ASSERTION,
    DISABLED_IGNORED_TEST.rule_id: DISABLED_IGNORED_TEST,
}
