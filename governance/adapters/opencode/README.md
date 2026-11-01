# OpenCode adapter

Map the five core roles to `.opencode/agent/<name>.md` files.

| Core role | Suggested agent file | Permission |
| :--- | :--- | :--- |
| `author` | `.opencode/agent/product_owner.md` | edit allow; no code paths |
| `builder` | `.opencode/agent/be_dev.md` and `.opencode/agent/fe_dev.md` | edit allow; worktree |
| `reviewer` | `.opencode/agent/reviewer.md` | edit deny |
| `qa` | `.opencode/agent/qa_analyst.md` | edit deny; command allow |

A project MAY add its own writer or spec-reviewer agent. Map it in `PROJECT.md`
`## Agent map`; the core does not own your agent topology.

## Wiring

1. Keep `AGENTS.md` and `PROJECT.md` at the repository root. OpenCode reads the nearest `AGENTS.md`.
2. Put the role contract in the agent file. Keep the core role text in `governance/roles/`.
3. Bind the skills under `governance/skills/` in the agent file.
4. Give the reviewer and the QA a read-only permission block.
5. Add the harness worktree mode when the `worktrees` policy is `required`.

## Example permission block

```yaml
permission:
  edit: deny
  bash:
    "*": allow
  external_directory: deny
```

## Notes

- Do not copy `governance/` into `.opencode/`. Reference it.
- Do not let a builder run the full final gate. The parent runs it once.
