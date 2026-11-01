# sdd-gov in this project

Start here.

- Law: `AGENTS.md`
- Profile: `PROJECT.md`
- Specs: `specs/`
- Ledgers: `DECISIONS.md`, `KNOWN_ISSUES.md`, `RISKS.md`, `WORK.md`
- Memory: `MEMORY.md`
- Check: `./g check --budget`
- Context: `./g context --task <id>`
- Resume: `./g resume --spec <id>`
- Plan: `./g plan --spec <id>`
- Indexes: `./g emit all`
- Reserve: `./g reserve --size 10 --owner "team"`
- Metrics: `./g metrics --out .local/tmp/metrics.json`
- Doctor: `./g doctor`
- Upgrade: `./g upgrade --from <path>`
- Modules: `governance/MODULES.md`

The core is under `governance/`. Do not edit it. Project additions belong in the
project's own agent configuration, not in `governance/`.

The four core roles are `author`, `builder`, `reviewer`, and `qa`. Add your own
roles, skills, and docs in your harness. The `PROJECT.md` `## Agent map` section
records how your agents map to the four roles.
