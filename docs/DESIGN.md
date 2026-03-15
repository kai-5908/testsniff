# DESIGN

## Purpose

Summarize the product and engineering design principles that apply across the repository.

## Core Principles

- Rule-based detection over speculative or probabilistic analysis.
- Fast, parse-once architecture.
- High-signal findings with concrete remediation.
- Small, inspectable components instead of opaque pipelines.

## Current Design Posture

The project is still pre-implementation. Design work should focus on preserving explainability and precision in a static-only architecture before optimizing extensibility.

The authoritative v1.0.0 rule subset is defined in [docs/product-specs/rule-catalog-scope.md](/home/aoi_takanashi/testsniff/docs/product-specs/rule-catalog-scope.md). New rule work should align with that catalog before expanding scope.

## Design Boundaries

- The detector is not expected to use machine learning or probabilistic scoring.
- Unsupported smells should be documented as out of scope.
- Version 1 is limited to static analysis of Python source and related source artifacts.
- Reporting and rule semantics should be stable before editor integrations expand.

## Related Docs

- [ARCHITECTURE.md](/home/aoi_takanashi/testsniff/ARCHITECTURE.md)
- [docs/design-docs/core-beliefs.md](/home/aoi_takanashi/testsniff/docs/design-docs/core-beliefs.md)
- [docs/design-docs/technical-stack.md](/home/aoi_takanashi/testsniff/docs/design-docs/technical-stack.md)
- [docs/product-specs/rule-catalog-scope.md](/home/aoi_takanashi/testsniff/docs/product-specs/rule-catalog-scope.md)
