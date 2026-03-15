# PRODUCT SENSE

## Product Thesis

Python teams need a way to identify test smells they can trust. The product should prefer fewer findings with strong explanations over broad but noisy coverage.

## Target Users

- Maintainers improving long-lived Python test suites
- Teams adopting stricter quality gates in CI
- Contributors who need clear, teachable remediation guidance

## Product Risks

- Overpromising smell coverage before rule-based criteria are defined
- Producing output that feels academically correct but operationally weak
- Mixing structural linting with behavioral claims the tool cannot justify

## What Good Looks Like

- Findings are precise enough to act on immediately.
- Teams can adopt the tool in CI without large suppression overhead.
- Rule explanations teach maintainable testing practices.
