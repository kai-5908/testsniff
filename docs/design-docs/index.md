# Design Docs Index

## Purpose

This index catalogs the design documents that define how the repository is operated and evolved.

Read only the relevant document for the task. Each entry records both decision status and validation status so agents can distinguish adopted guidance from open exploration.

## Catalog

| Document | Scope | Status | Validation |
| --- | --- | --- | --- |
| [core-beliefs.md](/home/aoi_takanashi/testsniff/docs/design-docs/core-beliefs.md) | Agent-first operating model and documentation beliefs | Adopted | Verified against bootstrap repo intent |
| [agent-operations.md](/home/aoi_takanashi/testsniff/docs/design-docs/agent-operations.md) | How agents should navigate, plan, and update docs | Proposed | Not yet enforced by tooling |
| [reporting-contract.md](/home/aoi_takanashi/testsniff/docs/design-docs/reporting-contract.md) | Canonical structure for lint-style findings | Proposed | Based on product target only |
| [technical-stack.md](/home/aoi_takanashi/testsniff/docs/design-docs/technical-stack.md) | Adopted implementation stack for version 1 | Adopted | Partially verified |
| [application-architecture.md](/home/aoi_takanashi/testsniff/docs/design-docs/application-architecture.md) | Concrete module boundaries and scan flow for version 1 | Adopted | Partially verified |
| [internal-quality-rules.md](/home/aoi_takanashi/testsniff/docs/design-docs/internal-quality-rules.md) | Internal architecture quality rules and enforcement expectations | Adopted | Conceptual |
| [branch-and-release-rules.md](/home/aoi_takanashi/testsniff/docs/design-docs/branch-and-release-rules.md) | Branching, versioning, and release rules for version 1 | Adopted | Partially verified |

## Status Definitions

- `Draft`: Early thinking, not yet accepted.
- `Proposed`: Candidate guidance awaiting implementation or confirmation.
- `Adopted`: Current source of truth.
- `Superseded`: Historical only; do not use for new work.

## Validation Definitions

- `Conceptual`: Reasoned design only.
- `Partially verified`: Some implementation or tests exist.
- `Verified`: Matches current implementation or repo policy.

## Maintenance Rules

- Every design doc must be linked here.
- New design docs should declare status and validation at the top.
- Superseded docs should link to the replacing document.
- Orphan design docs are not considered authoritative.
