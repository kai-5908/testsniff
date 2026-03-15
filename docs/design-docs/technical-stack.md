# Technical Stack

- Status: Adopted
- Validation: Partially verified

## Decision

Version 1 will use a Python-first implementation.

Selected stack:

- Runtime: Python 3.12+
- Project management: `uv`
- Build backend: `uv_build`
- CLI: `Typer`
- Static analysis: standard-library `ast` and `tokenize`
- Reporting: canonical finding model rendered as `human`, `compact`, and `json`
- Internal models: `dataclasses` with type hints
- Configuration: `pyproject.toml` via `tomllib`
- Testing: `pytest`
- Dev quality tools: `Ruff` and `ty`
- Optional terminal UX enhancement: `Rich`

## Why This Stack

- Python is the natural implementation language for Python test analysis.
- `ast` provides stable source positions and enough structure for version 1 static rules.
- `tokenize` complements `ast` for source-level checks such as comment-aware rules.
- `uv` keeps environment management, tool execution, and packaging aligned with the rest of the chosen ecosystem.
- `dataclasses` are sufficient while the config and finding schemas are still evolving.

## Explicit Non-Choices For Version 1

- No Rust core for initial implementation.
- No mandatory `LibCST` dependency.
- No mandatory `Pydantic` dependency.
- No database or daemon process.

## Revisit Conditions

Reconsider these choices if any of the following become true:

- Static rule count grows enough that parse and traversal time become a bottleneck.
- Editor integration requires always-on low-latency incremental analysis.
- Product scope expands beyond static analysis.
- Configuration or plugin APIs become complex enough that stronger validation and schema generation are worth the added weight.

## Consequences

- Architecture can stay as a static-only modular monolith in version 1.
- The canonical `Finding` model only needs to represent source-backed findings in version 1.
- External integrations should prefer the CLI plus JSON output rather than importing unstable internal modules.
