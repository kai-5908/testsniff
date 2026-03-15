# RELIABILITY

## Objective

Define how the tool should behave predictably and safely as it matures.

## Reliability Principles

- The same inputs and rule configuration should yield the same findings.
- Parser failures should degrade clearly, not silently.
- Unsupported constructs should be reported or skipped deliberately.
- Rule-level regressions should be caught by fixtures and snapshot tests.
- Confidence levels should reflect the strength of the static rule, not hidden heuristics.

## Current Strategy Boundary

The reliability strategy now covers both:
- external behavior
- internal architecture quality

Detailed internal rules are defined in [docs/design-docs/internal-quality-rules.md](/home/aoi_takanashi/testsniff/docs/design-docs/internal-quality-rules.md).

Covered now:
- finding correctness as observed by users
- output stability for `human`, `compact`, and `json`
- exit code stability
- confidence semantics for static findings
- layer boundaries and orchestration responsibilities
- canonical model stability and rule testability

## External Quality Strategy

Version 1 should protect the external contract through the following controls:

- Positive and negative fixtures for each rule
- Golden-output snapshots for `human`, `compact`, and `json`
- Contract checks for rule IDs, exit codes, and JSON shape
- Explicit review of `WHY`, `FIX`, and `EXAMPLE` content as product behavior
- Performance smoke tests to confirm the CLI remains usable in day-to-day workflows

## Release Gates For External Quality

- `high` confidence rules should have complete positive and negative fixtures plus stable output snapshots
- `medium` confidence rules may ship, but must document their evidence basis and remain non-surprising in default output

## Internal Quality Strategy

Version 1 should protect internal quality through the following rules:

- Keep `cli`, `services`, `parser`, `rules`, and `reporting` responsibilities separated
- Treat `ScanConfig`, `ModuleContext`, `Finding`, and `ScanResult` as internal contracts
- Require each rule to remain testable in isolation from I/O
- Add regression tests for every bug fix
- Enforce layer-specific test coverage and architecture checks as the codebase appears

The detailed rule set lives in [docs/design-docs/internal-quality-rules.md](/home/aoi_takanashi/testsniff/docs/design-docs/internal-quality-rules.md).

## Expected Failure Modes

- Syntax errors in target files
- Parser representation gaps
- Incorrect source location chosen for cross-node findings
- Rule overlap causing duplicate or contradictory findings
- Drift between rule behavior and documented remediation

## Planned Controls

- Positive and negative fixtures per rule
- Formatter snapshot tests
- Stable exit code contract
- Documentation review when rule behavior changes
- Architecture tests for import boundaries when the initial code structure exists
- Regression tests for every defect fix
