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
- [docs/design-docs/issue-management-rules.md](/home/aoi_takanashi/testsniff/docs/design-docs/issue-management-rules.md): GitHub Issue structure and task granularity rules.
- [docs/design-docs/pull-request-rules.md](/home/aoi_takanashi/testsniff/docs/design-docs/pull-request-rules.md): Pull request structure, verification, and review rules.
- [docs/design-docs/issue-to-plan-workflow.md](/home/aoi_takanashi/testsniff/docs/design-docs/issue-to-plan-workflow.md): Required workflow for fetching an issue, drafting a Japanese execution plan, and waiting for approval.
- [docs/design-docs/git-operation-skill-rules.md](/home/aoi_takanashi/testsniff/docs/design-docs/git-operation-skill-rules.md): Required repo-local skills for git pull, commit, and push.
- [docs/design-docs/local-git-hook-rules.md](/home/aoi_takanashi/testsniff/docs/design-docs/local-git-hook-rules.md): Local pre-commit and pre-push hook policy.
- [issue-to-plan skill](/home/aoi_takanashi/testsniff/.codex/skills/issue-to-plan/SKILL.md): Local skill for issue-driven planning before implementation.
- [code-review skill](/home/aoi_takanashi/testsniff/.codex/skills/code-review/SKILL.md): Local skill for general software engineering review plus testsniff-specific review checks.
- [security-review skill](/home/aoi_takanashi/testsniff/.codex/skills/security-review/SKILL.md): Local skill for threat-focused security review of code, config, and design changes.
- [pull skill](/home/aoi_takanashi/testsniff/.codex/skills/pull/SKILL.md): Local skill for merge-based branch updates.
- [commit skill](/home/aoi_takanashi/testsniff/.codex/skills/commit/SKILL.md): Local skill for scoped conventional-style commits.
- [push skill](/home/aoi_takanashi/testsniff/.codex/skills/push/SKILL.md): Local skill for pushing topic branches and updating PRs.
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

For issue-driven implementation work:
1. Fetch the issue first.
2. Use the local `issue-to-plan` skill.
3. Create or update a Japanese execution plan under `docs/exec-plans/active/`.
4. Share the plan and wait for human approval before implementation.

For git operations:
1. Use the local `pull` skill for branch updates.
2. Use the local `commit` skill for commits.
3. Use the local `push` skill for push and PR updates.

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
