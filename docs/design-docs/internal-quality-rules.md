# Internal Quality Rules

- Status: Adopted
- Validation: Conceptual

## Goal

Define the internal quality rules that protect the version 1 static application architecture from erosion.

## Scope

These rules apply to:
- module boundaries
- core data contracts
- testing expectations
- review and change-management expectations

They are intended to keep the codebase modular, testable, and safe to change.

## Core Principle

The main internal-quality goal is to preserve clear boundaries:
- `cli` owns user interaction
- `services` owns orchestration
- `parser` owns source analysis primitives
- `rules` own smell detection
- `reporting` owns output rendering

If these boundaries blur, internal quality is considered to have regressed.

## Architectural Rules

### Rule 1: `cli` must depend on `services`, not on concrete rules

The CLI may construct a scan request and render the final result, but it must not coordinate rule execution directly.

### Rule 2: `rules` must be pure with respect to I/O

Rules must not:
- read files directly
- print output
- inspect CLI arguments
- mutate global process state

Rules should consume `ModuleContext` and emit findings only.

### Rule 3: `parser` must remain shared infrastructure

The parser layer may provide reusable indexes and source helpers, but it must not contain rule-specific decisions.

### Rule 4: `reporting` must not decide whether a smell exists

The reporting layer may format findings, but it must not add rule logic, hide required fields, or reinterpret rule semantics.

### Rule 5: `config` must normalize configuration before scan execution

Configuration parsing and defaulting should be complete before the parser or rule engine starts work.

### Rule 6: cross-layer shortcuts are prohibited

Examples of prohibited shortcuts:
- `rules` importing `cli`
- `reporting` importing AST traversal helpers
- `config` importing concrete rule modules to infer defaults

## Data Contract Rules

### Rule 7: canonical models are first-class contracts

The following internal models are contracts:
- `ScanConfig`
- `ModuleContext`
- `Finding`
- `ScanResult`

Changes to these models require:
- tests updated or added
- affected docs updated
- explicit review of compatibility impact

### Rule 8: `Finding` must be complete before reporting

Renderers should receive normalized findings, not partial findings that they have to repair.

### Rule 9: `ModuleContext` is the only rule input boundary

Rules should not re-open files or rebuild ASTs. If a rule needs extra reusable structure, that structure should be added to parser-owned indexes or helpers.

## Testing Rules

### Rule 10: each layer must have its own tests

Minimum test expectations:
- `config`: unit tests for defaults, overrides, and invalid input
- `parser`: unit tests for loading, AST parsing, token extraction, and source positions
- `rules`: positive and negative fixtures per rule
- `reporting`: snapshot tests for `human`, `compact`, and `json`
- `services`: end-to-end orchestration tests

### Rule 11: every bug fix must add a regression test

The preferred regression mechanism is a fixture or snapshot that would have failed before the fix.

### Rule 12: boundary rules should be tested directly

The repository should eventually include architecture tests that enforce import boundaries and prevent layer leakage.

## Review Rules

### Rule 13: new rules are incomplete without metadata and fixtures

A new smell rule is not complete unless it includes:
- rule metadata
- positive fixture
- negative fixture
- expected output coverage when formatting is affected

### Rule 14: helpers must move to the correct layer

If logic becomes shared across multiple rules, it should be promoted into parser or rule helper modules instead of duplicated.

### Rule 15: convenience is not a reason to violate boundaries

Short-term speed is not a valid reason to move orchestration into `cli`, rule semantics into `reporting`, or file I/O into `rules`.

## CI Expectations

The intended minimum internal-quality gate is:
- `ruff`
- `ty`
- unit tests
- integration tests
- snapshot tests
- architecture tests when introduced

## Definition Of Internal Quality Regression

Internal quality should be treated as regressed when any of the following occurs:
- layer boundaries are crossed without explicit redesign
- a canonical model changes without coordinated test and doc updates
- a rule becomes difficult to test in isolation
- output rendering begins to contain rule semantics
- parser helpers become rule-specific and non-reusable

## Related Docs

- [docs/design-docs/application-architecture.md](/home/aoi_takanashi/testsniff/docs/design-docs/application-architecture.md)
- [ARCHITECTURE.md](/home/aoi_takanashi/testsniff/ARCHITECTURE.md)
- [docs/RELIABILITY.md](/home/aoi_takanashi/testsniff/docs/RELIABILITY.md)
