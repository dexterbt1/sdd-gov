---
name: kickoff
description: Run the project kickoff interview to establish context, scope, architecture, risk, and measures before any significant work.
---

# Kickoff

Use this skill when a project starts, when a cross-layer program starts, or when a change touches a domain entity, an API contract, an auth boundary, or a security control.

## Method

1. Read `governance/KICKOFF.md`.
2. Ask one round at a time. Number every question.
3. Give a recommended answer for every question.
4. Wait for the human answer. Do not answer for the human.
5. Record each answer in the named artifact.
6. Mark each statement `Observed`, `Given`, `Assumed`, `Estimated`, `Recommended`, or `Open`.

## Output

- `PROJECT.md` with context, goals, non-goals, layers, constraints, and collaboration.
- `DECISIONS.md` with one `proposed` row per open decision.
- `RISKS.md` with one row per accepted risk.
- `WORK.md` with the MVP items.
- `specs/0001-<feature>.md` with the first user story.

## Readiness gate

The kickoff is complete only when `PROJECT.md` has no placeholder, each open decision has an owner and a date, the MVP scope has acceptance criteria, and `govern.py check` passes.

Do not start implementation before the gate passes.
