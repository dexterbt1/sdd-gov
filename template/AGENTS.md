# AGENTS.md

This project uses sdd-gov. Read `PROJECT.md` for the project profile.

## The 10 invariants

1. One spec owns every change. Spec IDs are immutable.
2. Every requirement has a stable `REQ-<spec>-<nn>` ID and an RFC 2119 level.
3. Every requirement links a `@spec:<spec>-REQ-<nn>` test tag or is marked `(non-testable)`.
4. One fact has one home. Indexes and reports are generated, never hand-maintained.
5. The author does not review their own work. Review uses a fresh context.
6. Verify the real artifact, never a self-report.
7. Automated gates fail closed. Prose rules are advisory.
8. Scope isolation, secrets, and migrations are declared in `PROJECT.md` and enforced by hooks.
9. Decisions are recorded before code and adjudicated by a human.
10. Agents write only inside the active worktree.

The invariants are non-weakenable. A project may add rules. It may not remove them.

## The 4 roles

- `author` writes the spec, the decisions, and the acceptance criteria.
- `builder` writes code test-first and runs targeted tests.
- `reviewer` checks the spec or the implementation in a fresh context. Read-only.
- `qa` verifies behavior and captures evidence.

Role contracts live in `governance/roles/` inside `sdd-gov/`.

A project MAY add a role in its own harness. The core does not prescribe your
agent topology. Record the mapping in `PROJECT.md` under `## Agent map`.

The `builder` is one contract. Specialize it with layer skills or separate harness
agents. The `reviewer` has `SPEC_REVIEW` and `IMPLEMENTATION_REVIEW` modes. Map
them to one agent or two.

## Session protocol

1. Read `PROJECT.md` and `MEMORY.md`.
2. From the project root, run `sdd-gov/g` for structured facts. In the root layout, use `python3 governance/scripts/govern.py`.
3. For normative text, read the named spec section only.
4. Start work with `sdd-gov/g context --task <id>` or `sdd-gov/g resume --spec <id>`.
5. Before signoff, run `sdd-gov/g check --budget`.

## Retrieval contract

- Do not load the full corpus.
- Do not read a progress log. There is none.
- Use `sdd-gov/g find`, `show`, `search`, `deps`, and `impact` to locate facts.
- A context bundle is regenerable. After a compaction, run `resume` or `context` again.

## Gates

- `sdd-gov/g check` fails closed on a missing tag, a broken reference, a budget breach, or a task cycle.
- The reviewer and QA roles are read-only.
- A phase allows one review plus one re-review. A new blocker permits one final targeted re-review.

## Worktrees

The policy is in `PROJECT.md` under `worktrees`. The core rule is one writer per
worktree. Use a worktree when two or more builders work at the same time.

## Decisions

Record a decision in `DECISIONS.md` before the code. A decision has a human owner,
a date, and a status. Do not create a second decision log.
