# sdd-gov

A small, non-weakenable governance core for spec-driven development with AI coding agents.

## What it is

sdd-gov gives a project a durable spine:

- One spec owns every change.
- Every requirement has a stable ID and a test tag.
- Independent review uses a fresh context.
- Automated gates fail closed.
- Indexes, traceability, and release notes are generated, not hand-maintained.

The core is stack-agnostic. A project declares its stack, layers, commands, and
risks in `PROJECT.md`. The core never needs an edit.

## Why

Agentic projects drift in predictable ways: the spec falls behind the code, the
same fact lives in three files, and a long session forgets what the project
decided. sdd-gov removes the duplicate state and makes the remaining state
machine-checkable.

The design does not promise speed. It targets lower variance, less rework, and
auditable decisions.

## Quickstart: agent-mediated

Give an agent this instruction:

> Adopt the governance at `https://github.com/<org>/sdd-gov` at tag `v0.4.0`. Read
> `ADOPT.md` and follow it exactly. Do not copy a file it does not name. Ask before
> overwriting anything that exists.

## Manual adoption

```sh
git clone --depth 1 --branch v0.4.0 https://github.com/<org>/sdd-gov .local/tmp/sdd-gov
python3 .local/tmp/sdd-gov/governance/scripts/govern.py init --from .local/tmp/sdd-gov
sdd-gov/g check --budget
```

The default layout is isolated. The core and the project record live under
`sdd-gov/`. One root `AGENTS.md` points to them.

Then run the kickoff in `sdd-gov/governance/KICKOFF.md`.

## Greenfield

Use the repository as a template, or run `init`. The `template/` directory holds
the files a new project receives.

## Brownfield

1. Clone the pinned tag.
2. Run `govern.py init --from <path>`.
3. Run `sdd-gov/g baseline`. This grandfathers existing specs and missing tags.
4. Run `sdd-gov/g check --budget`. New drift still fails.
5. Run the kickoff and record the discovered standards under `Observed`.

## Repository layout

```
ADOPT.md             the agent-facing adoption protocol
AGENTS.md            how to work on sdd-gov itself
governance/          the vendored core (do not edit per project)
template/            the files copied into an adopting project
examples/            a passing greenfield example, a brownfield baseline, and a scribe reference
ci/                  GitHub and GitLab templates
```

## Adopted project layout

```
<project-root>/
├── AGENTS.md          one pointer to sdd-gov/AGENTS.md
└── sdd-gov/
    ├── g              POSIX wrapper
    ├── g.cmd          Windows wrapper
    ├── README.md      start here
    ├── AGENTS.md      the law
    ├── PROJECT.md     the per-project profile
    ├── MEMORY.md      bounded, source-cited memory
    ├── DECISIONS.md   the decision ledger
    ├── KNOWN_ISSUES.md
    ├── RISKS.md
    ├── WORK.md
    ├── governance/    the vendored core
    └── specs/
```

The source clone stays under `.local/tmp/sdd-gov/` and is deleted after install.

## The model

- **10 invariants.** `governance/invariants.md`.
- **4 roles.** author, builder, reviewer, qa. `governance/roles/`.
- **5 gates.** intake, spec, build, review, qa and complete. `governance/workflow.md`.
- **5 ledgers.** specs, decisions, known issues, risks, work.
- **Base modules.** `domain` (enforced when enabled) and `ste` (optional).
- **Shipped P1 modules.** `qa`, `provenance`, `database`, `isolation`, `api`, `security` — all opt-in.
- **Shipped P2 modules.** `bands`, `epic`, `metrics-export`, `matrix` — all opt-in.
- **Module reference.** `governance/MODULES.md`.
- **Derived views.** registry, traceability, release notes, indexes, plan waves, metrics.

A project owns its agent topology. The core does not prescribe where project roles,
skills, or docs live. Record the mapping in `PROJECT.md` `## Agent map`.

## Commands

```sh
sdd-gov/g check --budget
sdd-gov/g check --changed
sdd-gov/g idea "Offline sync"
sdd-gov/g context --task T-0001-01
sdd-gov/g resume --spec 1
sdd-gov/g plan --spec 1
sdd-gov/g next --spec 1
sdd-gov/g find --file src/app.py
sdd-gov/g metrics
sdd-gov/g emit all
sdd-gov/g emit registry --by-epic
sdd-gov/g reserve --size 10 --owner "platform team"
sdd-gov/g metrics --out .local/tmp/metrics.json
sdd-gov/g doctor --upstream <path>
sdd-gov/g upgrade --from <path>
sdd-gov/g selftest
```

In the root layout, run `python3 governance/scripts/govern.py` instead of `sdd-gov/g`.

## Design principles

1. One fact, one home. Everything else is generated or linked.
2. Machines enforce. People decide.
3. The core is small, stable, non-weakenable, and free of stack opinions.
4. The project owns its stack, agents, docs, and modules.
5. The session context is O(changed), not O(history).
6. A role is a contract, not a personality.
7. The definition of done is executable.
8. Optimize for a weak model: templates, checklists, narrow tools, fail-closed gates.

## What it is not

- Not a runtime, a daemon, or a hosted service.
- Not a replacement for code review, tests, or a human product owner.
- Not a UX review tool. The core omits visual and browser-based UX testing.
- Not a documentation system. A project adds its own writer role and docs.
- Not a promise of productivity. Measure locally with `govern.py metrics`.

## License

MIT.
