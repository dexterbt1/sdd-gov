# Generic adapter

A harness maps five core roles to its own agent or mode names.

| Core role | Harness slot | Required behavior |
| :--- | :--- | :--- |
| `author` | planner or architect | Writes specs and decisions. Never writes code. |
| `builder` | coder or implementer | Writes tests first. Runs targeted tests. |
| `reviewer` | reviewer or critic | Read-only. Fresh context. Returns a verdict. |
| `qa` | verifier or tester | Verifies the real artifact. Captures evidence. |

The core has four roles. A project MAY add its own role, for example a writer or a
spec-reviewer, in its harness. Record the mapping in `PROJECT.md` `## Agent map`.

## Binding rules

- The harness MUST give the `reviewer` and `qa` read-only access.
- The harness MUST run a builder in a worktree when the policy requires it.
- The harness MUST expose the project root as the only write scope.
- The harness MUST load `AGENTS.md` and `PROJECT.md` at session start.
- The harness SHOULD expose `governance/skills/*/SKILL.md` through progressive disclosure.

## Minimal mapping

If the harness has no roles, use one agent and run the gates in sequence. The
separation still holds: the agent that writes a change does not approve it.
