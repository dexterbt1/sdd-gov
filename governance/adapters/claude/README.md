# Claude adapter

Claude Code reads `AGENTS.md` and `CLAUDE.md`. Skills use the `SKILL.md` format.

## Mapping

| Core role | Claude slot |
| :--- | :--- |
| `author` | a planner subagent |
| `builder` | a coder subagent |
| `reviewer` | a read-only reviewer subagent |
| `qa` | a read-only verifier subagent |

A project MAY add its own writer or spec-reviewer subagent. Map it in `PROJECT.md`
`## Agent map`.

## Wiring

1. Put `AGENTS.md` at the repository root. Add a `CLAUDE.md` that points to it.
2. Put each role in `.claude/agents/<role>.md`.
3. Put each skill in `.claude/skills/<name>/SKILL.md`, or reference `governance/skills/`.
4. Use the frontmatter fields `name` and `description` for each skill.
5. Keep the reviewer and the QA read-only.

## Notes

- Claude Code loads a skill by description. Keep the description specific.
- Do not create a second copy of the invariants. Point to `governance/invariants.md`.
