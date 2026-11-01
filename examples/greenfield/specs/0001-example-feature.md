---
id: 1
title: Greeting feature
status: completed
layer: [backend, frontend]
epic: 1
owner: author
trust_boundary: false
size: standard
depends_on: []
decision_refs: [DEC-0001-01]
issue_refs: [KI-0001-01]
entities: [Greeting]
touches: ["src/**", "tests/**"]
created: 2026-01-01
updated: 2026-01-15
---

# Spec 0001: Greeting feature

## Context

A small example that proves the governance path end to end.

## Scope

### In scope

- A greeting function.
- A test for the greeting.
- A deferred localization note.

### Out of scope

- Localization.

## Requirements (REQ-0001)

### `REQ-0001-01`: Greeting function

- The system MUST return a greeting string.

### `REQ-0001-02`: Greeting test

- A test MUST cover the greeting.

### `REQ-0001-03`: Localization (non-testable)

- Localization is deferred to a later spec.

## Acceptance Criteria

- `greet("Ada")` returns `Hello, Ada!`.
- The test carries the traceability tags.

## Tasks

| ID | Task | REQ | Depends on | Files | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| T-0001-01 | Add the greeting function | REQ-0001-01 | — | src/greet.py | done |
| T-0001-02 | Add the greeting test | REQ-0001-02 | T-0001-01 | tests/test_greet.py | done |
| T-0001-03 | Write the localization note | REQ-0001-03 | — | docs/greet.md | done |

## Verification

| Requirement | Test | Level |
| :--- | :--- | :--- |
| REQ-0001-01 | `@spec:0001-REQ-01` | unit |
| REQ-0001-02 | `@spec:0001-REQ-02` | unit |
| REQ-0001-03 | (non-testable) | manual |
