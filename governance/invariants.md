# Invariants

The 10 invariants are the non-weakenable core. A project MAY add a rule. It MUST NOT remove or soften one.

| ID | Invariant | Rationale | Enforcement |
| :--- | :--- | :--- | :--- |
| `INV-01` | One spec owns every change. Spec IDs are immutable. | A stable owner makes traceability possible. | `govern.py check`; filename and frontmatter `id` match |
| `INV-02` | Every requirement has a stable `REQ-<spec>-<nn>` ID and an RFC 2119 level. | Atomic requirements are testable and searchable. | `govern.py check`; requirement headings |
| `INV-03` | Every requirement links a `@spec:<spec>-REQ-<nn>` test tag or is marked `(non-testable)`. | A requirement without a check is a wish. | `govern.py check`; test globs and tag pattern |
| `INV-04` | One fact has one home. Indexes and reports are generated, never hand-maintained. | Duplicate state drifts. | `govern.py emit`; `check` on generated views |
| `INV-05` | The author does not review their own work. Review uses a fresh context. | Self-review misses the same assumptions. | `reviewer` role; round cap |
| `INV-06` | Verify the real artifact, never a self-report. | A summary can hide a defect. | `reviewer` and `qa` roles; evidence |
| `INV-07` | Automated gates fail closed. Prose rules are advisory. | A rule a machine cannot check is a wish. | `govern.py check`; CI templates |
| `INV-08` | Scope isolation, secrets, and migrations are declared in `PROJECT.md` and enforced by hooks. | The core stays stack-agnostic; the project owns its risks. | `PROJECT.md`; `govern.py hooks` |
| `INV-09` | Decisions are recorded before code and adjudicated by a human. | The reason must survive the change. | `DECISIONS.md`; `check` cross-references |
| `INV-10` | Agents write only inside the active worktree. | Isolation prevents cross-worktree damage. | Role contracts; harness sandbox; review |

## Amending the invariants

The invariants change only with a new core version. A project MUST NOT edit this file to weaken a rule. A project MAY add a stricter rule in `PROJECT.md` or a module.

## The non-weakenable rule

A profile entry, a module, a skill, a role, or a hook MAY add a requirement or increase strictness. It MUST NOT disable traceability, independent review, fail-closed gates, or worktree containment. A project that needs a weaker rule MUST fork the core and record the fork. It MUST NOT hide the fork in `PROJECT.md`.
