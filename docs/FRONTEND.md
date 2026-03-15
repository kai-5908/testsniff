# FRONTEND

## Scope

There is no graphical frontend today. The primary user experience is the CLI output and any future editor integration built on top of it.

## UX Principles

- Findings should be readable in a terminal without extra tooling.
- The default formatter should resemble familiar lint tools.
- Important remediation details should fit within a narrow terminal width where possible.
- Future editor or CI integrations should reuse the same structured finding model.

## Near-Term UI Work

- Define stable output examples.
- Decide whether rule IDs appear in the default view.
- Specify any machine-readable formatter requirements before external integrations begin.
