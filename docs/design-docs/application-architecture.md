# Application Architecture

- Status: Adopted
- Validation: Partially verified

## Goal

Define the concrete version 1 application architecture for a static, rule-based Python test smell detector.

## Architectural Style

Version 1 uses a static-only modular monolith.

Key properties:
- one process
- one CLI entrypoint
- one canonical finding model
- clear boundaries between parsing, rule evaluation, and reporting

This is intentionally not a plugin platform, daemon, or distributed system.

## Top-Level Flow

```text
CLI
  -> Config Loader
  -> Target Resolver
  -> Source Loader
  -> AST Index Builder
  -> Rule Registry
  -> Rule Engine
  -> Finding Normalizer
  -> Reporter
  -> Exit Code Resolver
```

## Module Responsibilities

### `cli`

Responsible for:
- parsing command-line arguments
- selecting output format
- surfacing user-facing errors
- returning the final exit code

The CLI should call a single application service rather than coordinating rules directly.

### `config`

Responsible for:
- loading `pyproject.toml`
- applying defaults
- applying CLI overrides
- exposing a normalized scan configuration

Configuration should be validated lightly and converted into internal types before scan execution begins.

### `parser`

Responsible for:
- reading source files
- parsing them into Python ASTs
- collecting token streams when needed
- building reusable indexes for rules

The parser layer should parse each file at most once per scan.

### `rules`

Responsible for:
- declaring rule metadata
- deciding whether a rule applies
- evaluating rule logic against parsed modules
- emitting raw findings

Rules must not:
- print output
- read files directly
- mutate configuration
- depend on CLI concerns

### `reporting`

Responsible for:
- storing the canonical `Finding` model
- rendering findings in `human`, `compact`, and `json`
- ensuring the output contract is consistent across rules

### `services`

Responsible for:
- orchestrating the full scan use case
- coordinating parser, rule registry, and reporting
- returning a complete scan result

This is the application boundary that both the CLI and a future Python API should call.

## Proposed Package Layout

```text
src/testsniff/
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
    base.py
    registry.py
    checks/
      *.py
  reporting/
    finding.py
    render.py
    exit_codes.py
  services/
    scan.py
  docs/
    rule_metadata.py
```

## Core Data Structures

### `ScanConfig`

Represents normalized runtime configuration.

Expected fields:
- target paths
- include and exclude patterns
- selected rule IDs
- ignored rule IDs
- minimum confidence threshold
- minimum severity threshold
- output format

### `ModuleContext`

Represents all parsed information for one Python file.

Expected fields:
- absolute file path
- source text
- parsed AST
- token stream when needed
- helper indexes derived from the AST

This is the primary input object for static rules.

### `Rule`

Represents one smell detection rule.

Expected interface:

```python
class Rule(Protocol):
    rule_id: str
    default_severity: str
    default_confidence: str

    def analyze(self, module: ModuleContext) -> list[Finding]: ...
```

Rules may share helper functions, but each rule should remain independently testable.

### `Finding`

Represents the canonical output record.

Expected fields:
- `rule_id`
- `headline`
- `severity`
- `confidence`
- `engine`
- `path`
- `line`
- `column`
- `why`
- `fix`
- `example.bad`
- `example.good`
- `references`

In version 1, `engine` should always be `static`.

### `ScanResult`

Represents the full result of one scan.

Expected fields:
- findings
- files scanned
- files skipped
- parse failures
- elapsed time
- exit code

## Main Sequence

### 1. CLI Entry

The CLI parses arguments and builds a lightweight request object.

### 2. Config Resolution

The scan service loads `pyproject.toml`, applies defaults, then applies CLI overrides to produce `ScanConfig`.

### 3. Target Resolution

The scan service resolves Python test files from the provided paths and exclusion rules.

### 4. Parse Phase

Each target file is loaded once and converted into `ModuleContext`.

If parsing fails:
- the failure should be recorded
- the rest of the scan should continue where possible

### 5. Rule Selection

The registry resolves the enabled rules from the config.

### 6. Rule Evaluation

Each enabled rule receives each relevant `ModuleContext` and emits zero or more findings.

### 7. Finding Normalization

Findings are sorted and normalized before rendering so that repeated runs produce stable output.

### 8. Rendering And Exit Resolution

The reporter renders findings in the selected format and computes the final exit code.

## Rule Engine Strategy

The rule engine should be simple in version 1:
- iterate through files
- iterate through enabled rules
- collect findings

This is sufficient until profiling proves otherwise.

Optimizations that are acceptable later:
- pre-filtering rules by file characteristics
- sharing derived indexes across related rules
- parallel file processing

## Boundary Rules

These constraints should hold:

- `cli` depends on `services`, not on concrete rules
- `rules` depend on `parser` and `reporting` models, not on CLI code
- `reporting` depends on finding data, not on parser internals
- `config` should not import rule implementations directly

These constraints are treated as internal quality rules and are defined normatively in [docs/design-docs/internal-quality-rules.md](/home/aoi_takanashi/testsniff/docs/design-docs/internal-quality-rules.md).

## Error Handling Strategy

- Configuration errors should fail fast with a clear CLI error.
- Parse errors should be surfaced as scan diagnostics without crashing the whole run.
- Individual rule failures should be treated as tool defects and made visible during development.

Version 1 should prefer explicit failures over silent degradation when the tool itself is wrong.

## Testing Strategy By Layer

- `config`: unit tests for defaulting and overrides
- `parser`: unit tests for source loading, AST indexing, and token extraction
- `rules`: positive and negative fixtures per rule
- `reporting`: snapshot tests for `human`, `compact`, and `json`
- `services`: integration tests for end-to-end scan orchestration

## Deferred Concerns

These are intentionally deferred:
- runtime execution-based smells
- daemon mode
- third-party plugin API
- incremental persistent cache
- editor/LSP-specific architecture

## Related Docs

- [ARCHITECTURE.md](/home/aoi_takanashi/testsniff/ARCHITECTURE.md)
- [docs/design-docs/internal-quality-rules.md](/home/aoi_takanashi/testsniff/docs/design-docs/internal-quality-rules.md)
- [docs/design-docs/technical-stack.md](/home/aoi_takanashi/testsniff/docs/design-docs/technical-stack.md)
- [docs/design-docs/reporting-contract.md](/home/aoi_takanashi/testsniff/docs/design-docs/reporting-contract.md)
- [docs/RELIABILITY.md](/home/aoi_takanashi/testsniff/docs/RELIABILITY.md)
