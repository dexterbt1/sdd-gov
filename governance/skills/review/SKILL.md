---
name: review
description: Review a spec or an implementation in a fresh context and return one findings table with a verdict.
---

# Review

Use this skill in `SPEC_REVIEW` or `IMPLEMENTATION_REVIEW` mode.

## Method

1. Read the review packet.
2. Read the named spec sections.
3. For a spec review, check scope, requirements, acceptance criteria, tasks, traceability, domain, API, auth, security, and decisions.
4. For an implementation review, read the diff and the changed tests. Check requirement coverage, tags, scope, and security claims.
5. Run the targeted test command when the environment allows it.
6. Return one findings table and one verdict.

## Spec review checklist

- Scope matches the requirements, in both directions.
- Every requirement is testable, has one RFC 2119 level, and has a unique ID.
- Every requirement has an acceptance criterion.
- Every task links a requirement; no task invents a requirement.
- Every requirement has a test tag or `(non-testable)`.
- Dependencies are complete and acyclic.
- Every open decision has an owner; no decision is silently resolved.
- No requirement is ambiguous or contradictory.
- Every unstated assumption is recorded.
- The failure modes and boundaries are named.
- The domain, API, auth, and security declarations are present when required.
- A `specified` spec has no open question and at least one requirement.

## Finding format

`severity | file:line | requirement or authority | observed | expected | suggested fix`

## Rules

- Use a fresh context. Do not resume the implementer session.
- Do not trust a self-report. Inspect the real artifact.
- Do not edit or fix a file.
- Do not read the full corpus.
- Keep the report under 10,000 output tokens.
- One review plus one re-review. The re-review checks the prior findings and the changed lines only.
