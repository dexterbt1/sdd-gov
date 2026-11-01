# Codex adapter

Codex reads `AGENTS.md` from the repository root and from nested directories.

## Mapping

| Core role | Codex slot |
| :--- | :--- |
| `author` | a planning prompt or run |
| `builder` | a coding run |
| `reviewer` | a separate review run with a fresh context |
| `qa` | a separate verification run |

A project MAY add its own writing run or spec-review run. Map it in `PROJECT.md`
`## Agent map`.

## Wiring

1. Keep the root `AGENTS.md` short. It points to `PROJECT.md` and `governance/`.
2. Add a nested `AGENTS.md` in a package that needs a different policy. The nearest file wins.
3. Start each run with `govern.py context --task <id>` or `resume --spec <id>`.
4. Use a separate run for the review. Do not review in the build run.
5. Keep the review and the QA read-only.

## Notes

- Codex executes the commands in `AGENTS.md`. Keep each command exact.
- Do not put a secret in `AGENTS.md`.
