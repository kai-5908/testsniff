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

DUPLICATE_ASSERT = RuleMetadata(
    rule_id="TS005",
    headline="Test contains duplicated assertion",
    default_severity="error",
    default_confidence="high",
    why=(
        "Duplicated assertions add noise without increasing coverage, which makes tests harder "
        "to read and maintain."
    ),
    fix=(
        "Remove the repeated assertion or consolidate the repeated check into one clear "
        "verification per expectation."
    ),
    example=ExampleSnippet(
        bad=(
            "def test_user_creation(response):\n"
            '    assert response.status_code == 201\n'
            '    assert response.status_code == 201'
        ),
        good=(
            "def test_user_creation(response):\n"
            "    assert response.status_code == 201"
        ),
    ),
    references=(
        "docs/product-specs/rule-catalog-scope.md",
        "docs/exec-plans/completed/2026-03-22-ts005-duplicate-assert.md",
    ),
)
MAGIC_NUMBER_TEST = RuleMetadata(
    rule_id="TS006",
    headline="Test uses unexplained magic number in expectation",
    default_severity="warning",
    default_confidence="high",
    why=(
        "Hard-coded expectation numbers can hide intent, which makes tests harder to read and "
        "update when named constants or domain terms would be clearer."
    ),
    fix=(
        "Replace the bare numeric expectation with a named constant, enum, or helper that makes "
        "the expected meaning explicit."
    ),
    example=ExampleSnippet(
        bad=(
            "def test_status_code(response):\n"
            "    assert response.status_code == 200"
        ),
        good=(
            "from http import HTTPStatus\n\n"
            "def test_status_code(response):\n"
            "    assert response.status_code == HTTPStatus.OK"
        ),
    ),
    references=(
        "docs/product-specs/rule-catalog-scope.md",
        "docs/exec-plans/completed/2026-04-19-ts006-magic-number-test.md",
    ),
)

CONDITIONAL_LOGIC = RuleMetadata(
    rule_id="TS007",
    headline="Test contains conditional logic",
    default_severity="warning",
    default_confidence="high",
    why=(
        "Conditional branches make tests harder to read because the executed verification path "
        "depends on control flow inside the test body."
    ),
    fix=(
        "Split the scenarios into separate tests or move the branching setup into helpers so each "
        "test keeps one clear verification path."
    ),
    example=ExampleSnippet(
        bad=(
            "def test_user_status(user):\n"
            "    if user.is_admin:\n"
            '        assert user.role == "admin"'
        ),
        good=(
            "def test_admin_user_status(admin_user):\n"
            '    assert admin_user.role == "admin"'
        ),
    ),
    references=(
        "docs/product-specs/rule-catalog-scope.md",
        "docs/exec-plans/completed/2026-04-19-ts007-conditional-logic-in-tests.md",
    ),
)
RULE_METADATA_BY_ID: dict[str, RuleMetadata] = {
    EMPTY_TEST.rule_id: EMPTY_TEST,
    COMMENTS_ONLY_TEST.rule_id: COMMENTS_ONLY_TEST,
    MISSING_ASSERTION.rule_id: MISSING_ASSERTION,
    DISABLED_IGNORED_TEST.rule_id: DISABLED_IGNORED_TEST,
    DUPLICATE_ASSERT.rule_id: DUPLICATE_ASSERT,
    MAGIC_NUMBER_TEST.rule_id: MAGIC_NUMBER_TEST,
    CONDITIONAL_LOGIC.rule_id: CONDITIONAL_LOGIC,
}
