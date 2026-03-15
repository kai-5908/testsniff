# Rule Catalog Scope

- Status: Draft
- Intended user: Maintainers deciding whether a test smell belongs in the initial product scope

## Goal

Define the criteria for including a smell from the public catalog in this tool.

The project uses `rule-based` to mean:
- findings are produced by explicit logic and thresholds
- no machine-learned or probabilistic scoring is used as the decision mechanism

## Current Scope Boundary

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

## Deliverables

- A ratified rule catalog with included and excluded smells.
- Static detection signal for each supported smell.
- Initial severity and confidence policy per supported smell.
- Rationale for exclusions.
- Rule metadata template for future additions.
