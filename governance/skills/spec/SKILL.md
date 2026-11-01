---
name: spec
description: Author a spec with stable requirement IDs, RFC 2119 levels, acceptance criteria, and tasks linked to requirements and file scopes.
---

# Spec authoring

Use this skill when you write or amend a spec.

## Draft

For a raw idea, start with `govern.py idea "<title>"`. Fill `Problem`, `Options`,
`Open Questions`, `Assumptions`, and `Recommendation`. Do not add requirements yet.
Promote to `specified` when the open questions are closed and at least one
requirement exists.

## Method

1. Run the decision interview first when a material decision is open.
2. Write the context, the in-scope list, and the out-of-scope list.
3. Write each requirement as one heading: `### \`REQ-<spec>-<nn>\`: <title>`.
4. Give each requirement one RFC 2119 level.
5. Add an acceptance criterion for each requirement.
6. Add a task table. Each task has an ID, a requirement, a dependency list, a file scope, and a status.
7. Add a verification table that maps each requirement to a test tag or `(non-testable)`.
8. Run `govern.py check`.

## Rules

- One requirement is one testable statement.
- A requirement without a check is incomplete.
- A task with no file scope is not parallel-safe.
- Do not duplicate a decision, a limitation, or a risk. Link the ledger row.
- Keep a standard spec under 600 lines. Use `size: large` for 1,200 lines. Split above the hard ceiling.
