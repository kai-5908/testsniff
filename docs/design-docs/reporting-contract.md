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

- `Empty Test`: `severity=error`, `confidence=high`
- `Disabled / Ignored Test`: `severity=warning`, `confidence=high`
- `medium` is reserved for future threshold-driven structural rules; the current ratified v1.0.0 catalog does not use it.

## Output Modes

Version 1 should support three output modes:

- `human`: explanation-first default format
- `compact`: single-line lint-style format
- `json`: machine-readable format

All renderers must be derived from the same canonical finding model.

## Human Output Shape

Each finding should render with the following sections:

```text
error[TS001][confidence=high]: Test body is empty
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
tests/test_user_service.py:42:1: error[high] TS001 Test body is empty
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
      "headline": "Test body is empty",
      "severity": "error",
      "confidence": "high",
      "engine": "static",
      "location": {
        "path": "tests/test_user_service.py",
        "line": 42,
        "column": 1
      },
      "why": "Empty tests can pass without validating behavior, which creates false confidence in the test suite.",
      "fix": "Add a real assertion or remove the placeholder test until the intended behavior can be verified.",
      "example": {
        "bad": "def test_user_creation():\n    pass",
        "good": "def test_user_creation():\n    user = create_user(\"alice\")\n    assert user.name == \"alice\""
      },
      "references": [
        "docs/product-specs/rule-catalog-scope.md"
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
- The ratified v1.0.0 catalog currently uses `high` confidence only; any `medium` confidence rule needs explicit threshold rationale before it ships.
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
