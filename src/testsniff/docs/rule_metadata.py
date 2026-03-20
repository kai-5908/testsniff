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

RULE_METADATA_BY_ID: dict[str, RuleMetadata] = {
    EMPTY_TEST.rule_id: EMPTY_TEST,
    COMMENTS_ONLY_TEST.rule_id: COMMENTS_ONLY_TEST,
}
