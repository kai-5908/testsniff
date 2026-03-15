# SECURITY

## Scope

This project is expected to read source code and emit findings. It should not require elevated privileges or execute repository code during scanning.

## Security Principles

- Never execute scanned test code as part of smell detection.
- Treat repository input as untrusted text.
- Minimize filesystem writes during normal scans.
- Keep external network access out of the default scanning path.

## Early Security Questions

- Whether any parser dependency introduces code execution risk.
- How configuration files are discovered and validated.
- How future editor integrations handle workspace trust.

## Minimum Security Bar For Implementation

- Dependency choices documented and reviewed.
- Clear boundary between parsing and execution.
- Tests covering malicious or malformed input handling.
