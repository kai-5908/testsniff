# testsniff

`testsniff` is a static, rule-based Python test smell detector.

It scans Python test files, reports findings in a lint-style CLI format, and explains each finding with a reason, fix guidance, and example code. Version `0.1.0` is intentionally narrow: it supports static analysis only and currently ships with one implemented rule, `TS001` (`Empty Test`).

## Status

Current implementation on `main` includes:

- a working CLI entrypoint
- `pyproject.toml`-based configuration loading
- lint-style `human`, `compact`, and `json` output modes
- exit codes for success, findings, and scan failures
- one concrete rule: `TS001` (`Empty Test`)

## Installation

### Run from the repository with `uv`

```bash
uv sync
uv run testsniff --help
```

### Install the CLI locally

```bash
uv tool install .
testsniff --help
```

`testsniff` requires Python `3.12+`.

## Quick Start

Scan the default configured targets:

```bash
uv run testsniff scan
```

Scan an explicit path:

```bash
uv run testsniff scan tests
```

Choose a formatter:

```bash
uv run testsniff scan tests --format compact
uv run testsniff scan tests --format json
```

Run only specific rules or suppress a rule:

```bash
uv run testsniff scan tests --select TS001
uv run testsniff scan tests --ignore TS001
```

Filter findings by thresholds:

```bash
uv run testsniff scan tests --minimum-severity error --minimum-confidence high
```

## What Gets Scanned

By default, `testsniff` reads configuration from `[tool.testsniff]` in `pyproject.toml` and scans:

- `target_paths = ["tests"]`
- `include = ["test_*.py", "*_test.py"]`
- `exclude = [".venv/**", "build/**", "dist/**", "__pycache__/**"]`

Within matching files, the current implementation recognizes these test targets:

- top-level `pytest`-style `test_*` functions
- `test_*` methods on top-level `pytest`-style `Test*` classes
- `test_*` methods on statically resolvable `unittest.TestCase` subclasses

Nested helper functions and non-test helpers are excluded.

## Configuration

Example `pyproject.toml` configuration:

```toml
[tool.testsniff]
format = "human"
target_paths = ["tests"]
include = ["test_*.py", "*_test.py"]
exclude = [".venv/**", "build/**", "dist/**", "__pycache__/**"]
select = []
ignore = []
minimum_confidence = "medium"
minimum_severity = "info"
```

CLI options override the corresponding `pyproject.toml` values for the current run.

## Supported Rule

### `TS001` - Empty Test

Reports a test target whose body is empty after removing a leading docstring. In the current implementation, this means:

- no executable statements remain, or
- the remaining body is only `pass`

Default metadata:

- severity: `error`
- confidence: `high`

## Output

### Human

```text
error[TS001][confidence=high]: Test body is empty
  --> tests/test_example.py:1:1
  WHY: Empty tests can pass without validating behavior, which creates false confidence in the test suite.
  FIX: Add a real assertion or remove the placeholder test until the intended behavior can be verified.
  EXAMPLE:
    # Bad:
    def test_user_creation():
        pass
    # Good:
    def test_user_creation():
        user = create_user("alice")
        assert user.name == "alice"
  REFERENCES: docs/product-specs/rule-catalog-scope.md, docs/exec-plans/completed/2026-03-15-empty-test-rule.md
```

### Compact

```text
tests/test_example.py:1:1: error[high] TS001 Test body is empty
```

### JSON

```json
{
  "exit_code": 1,
  "files_scanned": 1,
  "files_skipped": 0,
  "findings": [
    {
      "confidence": "high",
      "headline": "Test body is empty",
      "location": {
        "column": 1,
        "line": 1,
        "path": "tests/test_example.py"
      },
      "rule_id": "TS001",
      "severity": "error"
    }
  ],
  "parse_failures": [],
  "tool": "testsniff",
  "version": "0.1.0"
}
```

## Exit Codes

- `0`: scan completed with no findings
- `1`: scan completed and findings were reported
- `2`: scan failed because at least one target file could not be parsed or read

## Development

Run the local checks:

```bash
uv run pytest
uv run ruff check .
```

## Scope Notes

`testsniff` currently focuses on explicit, explainable static rules. It does not execute tests and does not attempt probabilistic checks such as flaky-test detection or generic missing-assertion heuristics.

## Documentation

- Architecture: [ARCHITECTURE.md](ARCHITECTURE.md)
- Product rule scope: [docs/product-specs/rule-catalog-scope.md](docs/product-specs/rule-catalog-scope.md)
- Planning policy: [docs/PLANS.md](docs/PLANS.md)
