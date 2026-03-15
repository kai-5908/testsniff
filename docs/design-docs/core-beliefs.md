# Core Beliefs

- Status: Adopted
- Validation: Verified for current repository setup

## Why This Exists

This repository is intended to be usable by humans and coding agents without large hidden context. Documentation must support progressive disclosure and fast orientation.

## Beliefs

### 1. `AGENTS.md` is a map, not a dump

`AGENTS.md` should stay short and stable. It points to durable sources rather than duplicating them.

### 2. `docs/` is the repository memory

Important knowledge should live in versioned documents under `docs/`, not in chat history or undocumented conventions.

### 3. Plans are first-class artifacts

Meaningful work deserves a plan that survives the session. Active work, completed work, and deferred debt should all be discoverable in-repo.

### 4. Determinism beats coverage

For this product, a smaller set of trustworthy smell detections is better than a broader set of heuristic guesses.

### 5. Explanation is part of the product

A finding is incomplete if it only says what is wrong. It must also explain why the rule exists and how to fix the issue.

### 6. Indexes are mandatory

Agents should not need to brute-force the repository. Important document collections need explicit indexes.

### 7. Validation status must be visible

Readers need to know whether a document is describing current reality, a target design, or an unverified assumption.

### 8. Drift should be treated as a bug

Stale documentation creates operational risk. The long-term intent is to back these docs with linters and CI checks.

## Consequences

- New work should update the nearest relevant source of truth.
- Large design choices should be recorded in a durable document before they become ambiguous.
- Generated documents belong in a clearly marked location.
- Temporary notes should either graduate into durable docs or be removed.

## Non-Goals

- Keeping exhaustive prose in one entrypoint file.
- Documenting unsupported heuristics as if they were guarantees.
- Allowing critical operational knowledge to live only in issue threads.
