# Reporting Contract

- Status: Proposed
- Validation: Conceptual

## Goal

Define the canonical finding model and the default renderers for the test smell detector.

## Canonical Finding Fields

Every finding should carry the following fields before rendering:

- `rule_id`
- `headline`
- `severity`
- `confidence`
- `engine`
- `path`
- `line`
- `column` when available
- `why`
- `fix`
- `example.bad`
- `example.good`
- `references`

## Severity And Confidence

Severity and confidence are separate dimensions.

- `severity` answers: how serious is this issue if the finding is accepted?
- `confidence` answers: how strongly can the tool make this claim under the current rule?

Initial value sets:

- `severity`: `error`, `warning`, `info`
- `confidence`: `high`, `medium`

Examples:

- `Empty Test`: often `severity=error`, `confidence=high`
- `Magic Number Test`: often `severity=warning`, `confidence=high`
- `Long Test`: may be `severity=warning`, `confidence=medium` when it depends on explicit structural thresholds

## Output Modes

Version 1 should support three output modes:

- `human`: explanation-first default format
- `compact`: single-line lint-style format
- `json`: machine-readable format

All renderers must be derived from the same canonical finding model.

## Human Output Shape

Each finding should render with the following sections:

```text
warning[TS001][confidence=high]: Test has no assertions
  --> tests/test_user_service.py:42:1
  WHY: [rationale and reference]
  FIX: [concrete remediation guidance]
  EXAMPLE:
    # Bad:
    ...
    # Good:
    ...
```

## Compact Output Shape

Compact mode should emit a single line per finding:

```text
tests/test_user_service.py:42:1: warning[high] TS001 Test has no assertions
```

## JSON Output Shape

JSON mode should preserve the canonical model with minimal transformation:

```json
{
  "tool": "testsniff",
  "version": "0.1.0",
  "findings": [
    {
      "rule_id": "TS001",
      "headline": "Test has no assertions",
      "severity": "warning",
      "confidence": "high",
      "engine": "static",
      "location": {
        "path": "tests/test_user_service.py",
        "line": 42,
        "column": 1
      },
      "why": "Tests without assertions can pass while validating nothing.",
      "fix": "Add an explicit assertion or use pytest.raises/pytest.warns when that matches the intended behavior.",
      "example": {
        "bad": "def test_create_user():\n    create_user('alice')",
        "good": "def test_create_user():\n    user = create_user('alice')\n    assert user.name == 'alice'"
      },
      "references": [
        "https://example.invalid/rules/TS001"
      ]
    }
  ]
}
```

## Design Constraints

- The headline should be short and directly actionable.
- The location should resolve to a stable source line.
- `severity` and `confidence` must both be visible in `human` and `compact` output.
- Version 1 confidence values are limited to `high` and `medium`.
- `WHY` should explain the design intent behind the rule and link to the authoritative design source or ADR when available.
- `FIX` should prefer stepwise guidance over generic advice.
- `EXAMPLE` should show the smallest useful before-and-after snippet.
- Renderers must not silently drop structured finding fields that are available in the canonical model.

## Rule Metadata Requirements

Every rule should eventually provide:
- stable rule ID
- short headline
- default severity
- default confidence guidance
- long rationale
- fix guidance
- example bad snippet
- example good snippet
- reference links

## Open Questions

- Whether SARIF should ship in version 1 or be added after the canonical JSON schema stabilizes.
- Whether confidence should be user-configurable for some threshold-based static rules.
