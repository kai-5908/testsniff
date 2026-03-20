# Branch And Release Rules

- Status: Adopted
- Validation: Partially verified

## Goal

Define the repository rules for day-to-day branching, versioning, and releasing.

## Branch Strategy

Version 1 uses a simple trunk-based workflow.

### Rule 1: `main` is the only long-lived branch

The repository should not maintain a permanent `develop` branch or parallel long-lived release branches by default.

### Rule 2: work happens on short-lived topic branches

All implementation work should happen on short-lived branches that merge back into `main`.

Recommended naming:
- `feat/<topic>`
- `fix/<topic>`
- `docs/<topic>`
- `chore/<topic>`

Examples:
- `feat/empty-test-rule`
- `fix/config-threshold-filter`
- `docs/release-rules`

### Rule 3: parallel task work should use `git worktree`

When multiple tasks may proceed in parallel, each task should have its own `git worktree` rooted from `main`.

This repository treats a task-specific worktree as the default workspace for:
- implementation
- planning documents
- task-scoped documentation changes

Task worktrees should be created under `worktrees/` at the repository root, for example `worktrees/feat-empty-test-rule/`.

The primary checkout of `main` should remain available at the repository root as the stable source branch for creating new task worktrees.

### Rule 4: `main` should stay releasable

Changes merged into `main` should keep the repository in a releasable state.

At minimum this means:
- tests pass
- Ruff passes
- GitHub Actions CI remains green
- externally visible documentation stays in sync with behavior

### Rule 5: long-running branches require explicit justification

If a branch is expected to live for an extended period, that should be recorded in an execution plan or design decision, including why trunk-based work is not sufficient.

## Release Strategy

Version 1 uses tag-based releases from `main`.

### Rule 6: releases are cut from tagged commits on `main`

The source of truth for a release is a version tag on a `main` commit.

Recommended tag format:
- `v0.1.0`
- `v0.2.0`
- `v0.2.1`

### Rule 7: versioning follows Semantic Versioning, pre-1.0

The repository should use SemVer, with version numbers in the `0.y.z` range until the external contract is stable enough for `1.0.0`.

Interpretation for version 0:
- `0.y.0`: notable feature or external behavior expansion
- `0.y.z`: backward-compatible bug fix or packaging fix

### Rule 8: release builds should be created with `uv build`

Versioned distribution artifacts should be built from the tagged commit using the selected project tooling.

### Rule 9: releases are automated from GitHub tag events

The repository should use GitHub Actions to validate a tagged release, build artifacts, and publish the GitHub release.

## Pre-Release Checklist

Before creating a release tag, the maintainer should confirm:
- version numbers are updated where required
- `CHANGELOG.md` contains an entry for the target version
- user-facing docs are in sync with behavior
- `uv run ruff check src tests` passes
- `uv run pytest -q` passes
- `uv build` succeeds

## Post-Release Expectations

After a release:
- the tag should remain immutable
- any urgent fix should be prepared on a new topic branch and merged back to `main`
- the next version should be created from a fresh commit, not by mutating a prior tag

## When To Revisit This Strategy

The current strategy should be revisited if:
- multiple supported release lines are needed
- backporting becomes routine
- the project starts shipping frequent hotfixes against old versions
- CI/CD publishing and release automation become materially more complex

At that point, introducing `release/*` branches may become justified.

## Non-Goals

- Adopting GitFlow-style permanent branch hierarchy in version 1
- Maintaining multiple long-lived stabilization branches before there is evidence they are needed

## Related Docs

- [docs/design-docs/technical-stack.md](/home/aoi_takanashi/testsniff/docs/design-docs/technical-stack.md)
- [docs/design-docs/git-operation-skill-rules.md](/home/aoi_takanashi/testsniff/docs/design-docs/git-operation-skill-rules.md)
- [docs/PLANS.md](/home/aoi_takanashi/testsniff/docs/PLANS.md)
- [CHANGELOG.md](/home/aoi_takanashi/testsniff/CHANGELOG.md)
- [AGENTS.md](/home/aoi_takanashi/testsniff/AGENTS.md)
