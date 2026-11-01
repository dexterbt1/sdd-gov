# Upgrading

sdd-gov uses semantic versioning. In the isolated layout the core lives under
`sdd-gov/governance/`. In the root layout it lives under `governance/`.

## 0.4.0 notes

- The P2 modules are shipped: `bands`, `epic`, `metrics-export`, `matrix`.
- `reserve --size N` reserves a spec band.
- `emit registry --by-epic` groups the registry.
- `metrics --out <path>` writes the JSON export.

## 0.3.0 notes

- The six P1 modules are shipped: `qa`, `provenance`, `database`, `isolation`, `api`, `security`.
- ID widths are enforced. `DEC`, `KI`, `REQ`, and `T` follow `id_width`. `DEF`, `TP`, `RISK`, `EXC`, and `W` use four digits.
- A legacy `RISK-01`, `W-01`, or a 3-digit `DEC`/`KI` in a 4-digit project now fails.
- The `api` module requires PyYAML.

## What an upgrade changes

`sdd-gov/g upgrade --from <path>` replaces the files under `governance/`. It
preserves:

- `specs/`
- `PROJECT.md`
- `MEMORY.md`
- `DECISIONS.md`
- `KNOWN_ISSUES.md`
- `RISKS.md`
- `WORK.md`
- `AGENTS.md` (the full law)
- `README.md`
- `g` and `g.cmd`
- `governance/baseline.json`
- `governance/reservations.json`

An upgrade MUST NOT rewrite a spec, a ledger, a project profile, or the root
`AGENTS.md` pointer.

## Check for drift

```sh
sdd-gov/g doctor --upstream <path>
```

`doctor` reports the installed version, the upstream version, the install layout,
the project root, the worktree policy, an expired baseline, an expired budget
override, and a stale generated index.

## Upgrade order

1. Read `CHANGELOG.md`.
2. Run `doctor --upstream <path>`.
3. Run `upgrade --from <path>`.
4. Run `check --budget`.
5. Run `check --hooks` when the project defines hooks.
6. Commit the vendored core separately from the project files.

## Breaking changes

The major version changes when an invariant, a required frontmatter field, or a
required ledger column changes. A migration note lives in `CHANGELOG.md`. The note
names the old form, the new form, and the command or edit that closes the gap.

## Rollback

Keep the previous `governance/` directory or the previous commit. An upgrade is a
single directory replacement. Restore it to roll back. The project files are never
touched by an upgrade.
