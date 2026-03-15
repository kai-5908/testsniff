# Tech Debt Tracker

## Purpose

Track known debt that is acknowledged but not currently being executed as an active plan.

## Status Legend

- `open`: Known and not yet scheduled
- `planned`: Covered by an active plan
- `resolved`: Fixed and retained for history

## Debt Register

| ID | Status | Area | Summary | Notes |
| --- | --- | --- | --- | --- |
| TD-001 | open | Documentation automation | No doc linter or CI checks exist yet to enforce the knowledge base structure | Add after the initial codebase and CI foundation exist |
| TD-002 | open | Architecture | Parser technology choice is still undecided (`ast` vs `libcst` or equivalent) | Required before implementing line-precise rules |
| TD-003 | resolved | Product | Supported rule-based smell subset has not been ratified | Resolved by `docs/product-specs/rule-catalog-scope.md` and `docs/exec-plans/completed/2026-03-15-v1-rule-catalog.md` |
