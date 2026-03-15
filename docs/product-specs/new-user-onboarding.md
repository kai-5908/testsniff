# New User Onboarding

- Status: Draft
- Intended user: Python developer evaluating the tool on an existing test suite

## User Story

As a new user, I want to run the detector quickly on my repository and understand the findings without reading implementation details first.

## First-Run Expectations

- Installation is documented in one place.
- Running the default command on a project prints findings in a readable lint-style format.
- Each finding explains why it matters and how to fix it.
- A clean run returns a success exit code with minimal noise.

## Acceptance Criteria

- The default README or CLI help gives a copy-pasteable quickstart.
- The tool can target a path or default to the current project.
- Output examples in docs match the implemented formatter.
- False confidence is avoided: unsupported smells are not implied to be checked.

## Open Questions

- Whether onboarding should begin with a standalone binary, `uvx`, or a Python package install.
- Whether the first-run flow should suggest configuration when no test files are found.
