# AGENTS.md

This file is the repository map, not the encyclopedia.

Start here, then open only the smallest number of documents needed for the task.

## Repository Purpose

This repository will host a static, rule-based Python test smell detector.

Primary product goals:
- Detect only smells that can be identified through explicit static rule-based logic.
- Emit findings in a lint-style CLI format.
- Explain each finding with reason, fix guidance, and examples.

## Working Model

- `AGENTS.md` is the short entrypoint.
- `docs/` is the durable knowledge base.
- Plans are first-class artifacts and live in version control.
- Generated material belongs in `docs/generated/`.
- Documents should prefer stable links over repeated prose.

## Read In This Order

1. [ARCHITECTURE.md](/home/aoi_takanashi/testsniff/ARCHITECTURE.md)
2. [docs/design-docs/index.md](/home/aoi_takanashi/testsniff/docs/design-docs/index.md)
3. [docs/product-specs/index.md](/home/aoi_takanashi/testsniff/docs/product-specs/index.md)
4. [docs/PLANS.md](/home/aoi_takanashi/testsniff/docs/PLANS.md)
5. Active execution plans in [docs/exec-plans/active](/home/aoi_takanashi/testsniff/docs/exec-plans/active)

## Document Map

- [ARCHITECTURE.md](/home/aoi_takanashi/testsniff/ARCHITECTURE.md): Top-level package and domain map.
- [docs/design-docs/index.md](/home/aoi_takanashi/testsniff/docs/design-docs/index.md): Catalog of design docs and decision status.
- [docs/design-docs/technical-stack.md](/home/aoi_takanashi/testsniff/docs/design-docs/technical-stack.md): Adopted version 1 technology choices.
- [docs/design-docs/internal-quality-rules.md](/home/aoi_takanashi/testsniff/docs/design-docs/internal-quality-rules.md): Internal architecture quality rules and test expectations.
- [docs/design-docs/branch-and-release-rules.md](/home/aoi_takanashi/testsniff/docs/design-docs/branch-and-release-rules.md): Branching, versioning, and release rules.
- [docs/product-specs/index.md](/home/aoi_takanashi/testsniff/docs/product-specs/index.md): Product requirements and user journeys.
- [docs/DESIGN.md](/home/aoi_takanashi/testsniff/docs/DESIGN.md): Design principles and scope boundaries.
- [docs/FRONTEND.md](/home/aoi_takanashi/testsniff/docs/FRONTEND.md): UX guidance for CLI and future integrations.
- [docs/PLANS.md](/home/aoi_takanashi/testsniff/docs/PLANS.md): Planning policy and execution plan workflow.
- [docs/PRODUCT_SENSE.md](/home/aoi_takanashi/testsniff/docs/PRODUCT_SENSE.md): User value, constraints, and positioning.
- [docs/QUALITY_SCORE.md](/home/aoi_takanashi/testsniff/docs/QUALITY_SCORE.md): Quality rubric and gap tracking.
- [docs/RELIABILITY.md](/home/aoi_takanashi/testsniff/docs/RELIABILITY.md): Failure modes and operational expectations.
- [docs/SECURITY.md](/home/aoi_takanashi/testsniff/docs/SECURITY.md): Security boundaries and review expectations.
- [docs/exec-plans/tech-debt-tracker.md](/home/aoi_takanashi/testsniff/docs/exec-plans/tech-debt-tracker.md): Known debt register.
- [docs/generated/db-schema.md](/home/aoi_takanashi/testsniff/docs/generated/db-schema.md): Generated schema placeholder.
- [docs/references/](/home/aoi_takanashi/testsniff/docs/references): External reference snapshots for agents.

## Default Agent Workflow

1. Read this file.
2. Read the smallest relevant index document.
3. If the task is non-trivial, create or update an execution plan.
4. Make code or document changes.
5. Update affected docs before finishing.

## When To Update Docs

Update documentation in the same change when you modify:
- User-facing detection behavior.
- Rule IDs, message format, or remediation guidance.
- Package boundaries or data flow.
- Planning status or implementation milestones.
- Reliability, security, or quality assumptions.

## Plan Policy

- Small changes may use lightweight notes in the task thread.
- Complex work should create an execution plan under `docs/exec-plans/active/`.
- Completed plans move to `docs/exec-plans/completed/`.
- Known debt that is not being worked immediately goes to `tech-debt-tracker.md`.

## Validation Expectations

Every durable document should be:
- Linked from an index or map.
- Clear about status: draft, proposed, adopted, or superseded.
- Specific about what is verified versus assumed.
- Written so an agent can act without outside context.

## Current Project Status

Current state:
- Python package scaffold and tool configuration exist under `src/` and `pyproject.toml`.
- Minimal CLI, config loading, parsing, reporting, and scan orchestration are implemented.
- `TS001` (`Empty Test`) is implemented as the first concrete static rule.
- Local tests and Ruff checks exist, and GitHub Actions CI/release workflows are configured.
- Product scope is currently limited to static analysis.

## Expected Near-Term Docs To Add

- Rule catalog for supported rule-based smells.
- ADR log for rule semantics and output contract.
- CLI configuration reference.
- Contribution guide for adding rules and fixtures.

## If Information Conflicts

- Prefer implementation over stale prose.
- Prefer indexed documents over orphan files.
- Prefer newer execution plans over older assumptions.
- Record the conflict and fix the docs in the same change when feasible.
