# AGENTS.md

This is the sdd-gov repository. It is the governance core, not an adopted project.

Read `governance/invariants.md` first. The 10 invariants are the law of the core.

## Repository rules

- The core is non-weakenable. Do not remove or soften an invariant.
- `template/` is what an adopting project receives. `governance/` is the vendored core.
- The root `AGENTS.md` is for contributors to sdd-gov. `template/AGENTS.md` is the law for an adopted project.
- Keep the core stack-agnostic. A stack fact belongs in `PROJECT.md`, a hook, or a module.
- Do not add a brand or a vendor name to the core.
- Do not hardcode a project path outside the worktree.
- Keep the package dependency-free. `govern.py` uses the Python standard library only.

## Before a commit

```sh
python3 governance/scripts/govern.py selftest
python3 governance/scripts/govern.py check --root examples/greenfield --budget
python3 governance/scripts/govern.py check --root examples/brownfield --budget
```

## Versioning

- Bump `VERSION` and `governance/VERSION` together.
- Add a `CHANGELOG.md` entry.
- Run `govern.py manifest` to refresh `sdd-gov.json`.
- A breaking change to an invariant, a required field, or a ledger column is a major version.

## Adding a module or a capability

1. Add it under `governance/modules.d/` or `governance/skills/`.
2. Document it in `governance/composition.md`.
3. Add a check when the rule is machine-checkable.
4. Run the selftest.
