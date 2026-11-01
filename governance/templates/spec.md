---
id: {{ID}}
title: {{TITLE}}
status: {{STATUS}}
layer: [{{LAYER}}]
epic: {{EPIC}}
owner: {{OWNER}}
trust_boundary: false
size: standard
depends_on: []
decision_refs: []
issue_refs: []
touches: []
created: {{DATE}}
updated: {{DATE}}
---

# Spec {{ID_PADDED}}: {{TITLE}}

## Context

Describe the problem, the user, and why the change is needed.

## Scope

### In scope

- 

### Out of scope

- 

## Requirements (REQ-{{ID_PADDED}})

### `REQ-{{ID_PADDED}}-01`: First requirement

- The system MUST ...

## Acceptance Criteria

- The requirement is verified by a test or a manual check.

## Tasks

| ID | Task | REQ | Depends on | Files | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| T-{{ID_PADDED}}-01 | Implement the first requirement | REQ-{{ID_PADDED}}-01 | — | src/example.py | todo |

## Verification

| Requirement | Test | Level |
| :--- | :--- | :--- |
| REQ-{{ID_PADDED}}-01 | `@spec:{{ID_PADDED}}-REQ-01` | unit |
