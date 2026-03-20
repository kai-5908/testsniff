# Rule Catalog Scope

- Status: Adopted
- Intended user: Maintainers deciding whether a test smell belongs in the v1.0.0 product scope
- Success signal: A maintainer can decide whether a smell belongs in v1.0.0 and assign its initial severity and confidence without reopening scope debates.

## Goal

Ratify the v1.0.0 test smell catalog for `testsniff`.

The project uses `rule-based` to mean:
- findings are produced by explicit logic and thresholds
- no machine-learned or probabilistic scoring is used as the decision mechanism

## Version 1 Boundary

- `static`: source-only analysis using parsed code and related source artifacts
- `out-of-scope`: smells that require runtime observation, probabilistic modeling, or unsupported external evidence

## Inclusion Criteria

- The smell can be detected with explicit rule-based logic from source code and related source artifacts alone.
- The rule can point to a stable file and line.
- The rule can explain the risk and remediation concretely.
- The rule is expected to produce acceptable precision without project-specific training.

## Exclusion Criteria

- Rules that require runtime observation or test execution results.
- Rules that require probabilistic inference or model-based ranking.
- Rules that need unsupported external evidence or deep semantic knowledge beyond static analysis.
- Rules whose remediation cannot be made concrete enough for the default formatter.

## Rule ID Policy

- Implemented rules keep stable rule IDs.
- Unimplemented v1.0.0 rules may appear in this catalog by smell name before their final rule ID is assigned.
- Stable IDs for unimplemented rules are assigned in the follow-up implementation issue, not in this catalog change.

## Severity And Confidence Policy

- `severity` values for version 1 are `error`, `warning`, and `info`.
- `confidence` values for version 1 are `high` and `medium`.
- The ratified v1.0.0 catalog below uses `high` confidence only.
- `medium` remains available for future threshold-driven structural rules, but those rules are not part of the current v1.0.0 catalog.

## Ratified v1.0.0 Rules

| Smell | Rule ID | Static detection signal | Initial severity | Initial confidence | Why it is in scope |
| --- | --- | --- | --- | --- | --- |
| `Empty Test` | `TS001` | A standardized test target has no executable body after removing a leading docstring; v1 test targets are top-level `pytest`-style `test_*` functions, `test_*` methods on top-level pytest `Test*` classes, and statically resolvable `unittest.TestCase` `test_*` methods, while helpers and nested functions are excluded. | `error` | `high` | The signal is explicit, the reported location is stable, and the remediation is concrete. |
| `Missing Assertion` | `TS003` | A standardized test target has no recognized assertion signal in its executable body after excluding nested definitions; v1 recognized signals are bare `assert`, `unittest` instance calls whose method name starts with `assert` or is `fail`, and `pytest.raises(...)`, `pytest.warns(...)`, or `pytest.fail(...)` via explicit module or direct imports. | `error` | `high` | The rule remains static and explainable when limited to explicit assertion signals, and the remediation is concrete. |
| `Disabled / Ignored Test` | Assigned in a follow-up implementation issue | A test target is annotated with an explicit static skip or ignore mechanism that suppresses normal execution. | `warning` | `high` | The rule can be explained statically, reported at a stable decorator or test location, and gives actionable remediation. |

## Explicitly Excluded From v1.0.0

| Smell or smell group | Why it is excluded |
| --- | --- |
| `comments-only test` | Python does not treat comments as executable body content, so this is not a distinct Python rule separate from `Empty Test`. |
| broad `missing assertion` heuristics beyond explicit assertion signals | Helper-driven checks, dynamic assertions, and framework-specific matcher ecosystems require project-specific or semantic inference that version 1 still excludes. |
| `Magic Number Test` | Literal values in tests are often intentional test data, so the default remediation would be too context-dependent for a precise version 1 rule. |
| `Long Test` | The smell depends on project-specific thresholds and would start as a threshold-driven structural rule, which the current v1.0.0 catalog avoids. |
| runtime-observed smells such as flaky, slow, or order-dependent tests | They require execution or historical evidence and fall outside the static-only boundary. |

## Catalog Maintenance Rules

- Add a new smell to the catalog only if it satisfies the inclusion criteria above.
- Update this document in the same change that alters user-facing rule scope or initial severity/confidence policy.
- Keep excluded smells explicit when they are likely to be requested, so unsupported checks are not implied by omission.
