# Agent Operations

- Status: Proposed
- Validation: Conceptual

## Objective

Define how agents should work in this repository with minimal context loading and maximum traceability.

## Operating Rules

1. Start from [AGENTS.md](/home/aoi_takanashi/testsniff/AGENTS.md).
2. Open the narrowest relevant index before reading deep documents.
3. For non-trivial work, create or update an execution plan.
4. Change code and docs together when behavior changes.
5. Record unresolved debt in the debt tracker instead of leaving it implicit.

## Documentation Expectations

- Every durable document must have a clear home.
- Every collection of documents needs an index.
- Documents should say what is decided, what is assumed, and what is missing.
- References to external resources should be summarized or snapshotted when stability matters.

## Planned Automation

Future tooling should validate that:
- indexed documents exist
- status markers are present
- cross-links are not broken
- completed work is moved out of the active plan directory
- generated docs are not hand-edited without disclosure

## Open Items

- Exact linting rules for documentation structure.
- Frequency and mechanism for automated document hygiene scans.
