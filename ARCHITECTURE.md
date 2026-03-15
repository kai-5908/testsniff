# ARCHITECTURE.md

## Status

- Status: Draft
- Verification: Partially verified by the current project scaffold
- Last updated for: initial scaffold implementation

## Purpose

This document is the top-level map for the future codebase that will implement a static, rule-based Python test smell detector.

The repository currently contains documentation scaffolding only. The module structure below is the intended target architecture, not existing code.

## Architectural Principles

- Parse Python once and reuse intermediate indexes across checks.
- Keep detection rules rule-based and explainable.
- Separate rule logic from presentation formatting.
- Keep the implementation static-only in version 1.
- Treat fix guidance as product behavior, not incidental copy.
- Prefer a small core with explicit extension points.

## Proposed Package Map

```text
src/
  testsniff/
    cli/
      main.py
      arguments.py
    config/
      defaults.py
      loader.py
      types.py
    parser/
      loader.py
      ast_index.py
      tokens.py
      module_context.py
    rules/
      registry.py
      base.py
      checks/
        *.py
    reporting/
      finding.py
      render.py
    docs/
      rule_metadata.py
    services/
      scan.py
    compat/
      ruff_style.py
tests/
  fixtures/
  unit/
  integration/
```

## Layer Responsibilities

### `cli/`

Owns command-line entrypoints, exit codes, and user-visible formatter selection.

### `config/`

Owns local configuration, defaults, and lightweight validation. Rule enablement should resolve here before scan execution begins.

### `parser/`

Owns Python source loading and AST indexing. This layer should expose reusable query helpers so individual rules do not reimplement traversal logic.

### `rules/`

Owns rule metadata and smell detection logic. Rules should return structured findings and must not print or mutate files directly.

### `reporting/`

Owns the canonical finding model and translation into lint-style output. The target output must support:
- error headline
- severity and confidence
- file and line reference
- `WHY`
- `FIX`
- `EXAMPLE`

### `docs/`

Owns machine-readable rule metadata used to render consistent explanations. This is distinct from repository documentation under `docs/`.

### `services/`

Owns orchestration of config loading, parsing, rule execution, and reporting.

## Concrete Application Shape

Version 1 should be implemented as a static-only modular monolith with:
- one CLI entrypoint
- one scan orchestration service
- one canonical `Finding` model
- one parser pass per file

The detailed module boundaries and sequence are defined in [docs/design-docs/application-architecture.md](/home/aoi_takanashi/testsniff/docs/design-docs/application-architecture.md).

## Expected Data Flow

1. CLI resolves paths and configuration.
2. Parser loads Python test files and builds AST indexes.
3. Rule registry selects enabled static checks.
4. Rules emit normalized findings.
5. Reporting renders findings in the selected output format.
6. CLI returns a lint-like exit code.

## Domain Model Sketch

- `RuleId`: Stable identifier for a smell check.
- `Finding`: File path, line, column if available, headline, rationale, fix text, example block, severity, confidence, engine, and references.
- `RuleMetadata`: Human-facing explanation and references for a rule.
- `ScanTarget`: Resolved file set and applicable configuration.
- `ScanConfig`: Normalized configuration after defaults and CLI overrides are resolved.
- `ModuleContext`: Parsed source, tokens, and derived indexes for one module.
- `ScanResult`: Findings plus scan statistics and exit code.

## Cross-Cutting Concerns

- Performance: Avoid repeated parsing and whole-repository rescans when incremental input is possible.
- Explainability: Every finding should have concrete and reproducible reasoning.
- Rule-based scope: Unsupported probabilistic smells should be excluded rather than approximated.
- Testability: Every rule should ship with positive and negative fixtures.

## Chosen Technology Stack

- Python 3.12+
- `uv` and `uv_build`
- `Typer`
- standard-library `ast` and `tokenize`
- `dataclasses` and type hints for internal models
- `tomllib` for `pyproject.toml` configuration
- `pytest`, `Ruff`, and `ty` for development workflow

## Open Architectural Questions

- How should rule metadata be stored long term: Python, Markdown, or structured YAML/JSON?
- Which output modes are needed beyond `human`, `compact`, and `json`?
- How should line and column precision behave for multi-node smells?
- How should cross-function or cross-file static smells map to the most actionable source location?

## Related Docs

- [AGENTS.md](/home/aoi_takanashi/testsniff/AGENTS.md)
- [docs/design-docs/index.md](/home/aoi_takanashi/testsniff/docs/design-docs/index.md)
- [docs/design-docs/application-architecture.md](/home/aoi_takanashi/testsniff/docs/design-docs/application-architecture.md)
- [docs/design-docs/technical-stack.md](/home/aoi_takanashi/testsniff/docs/design-docs/technical-stack.md)
- [docs/DESIGN.md](/home/aoi_takanashi/testsniff/docs/DESIGN.md)
- [docs/RELIABILITY.md](/home/aoi_takanashi/testsniff/docs/RELIABILITY.md)
