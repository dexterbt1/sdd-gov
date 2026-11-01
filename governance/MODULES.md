# Modules

The core ships two base modules, six P1 modules, and four P2 modules. All are
opt-in. A project enables only what it needs.

## Base

| Module | Default | Adds |
| :--- | :--- | :--- |
| `domain` | enforced when enabled | Entity registry and declaration check |
| `ste` | optional | Simplified Technical English check |

## Shipped P1

| Module | Adds | Config keys |
| :--- | :--- | :--- |
| `qa` | Defect ledger and optional test plan | `qa_defects`, `qa_test_plan`, `qa_require_test_plan`, `qa_negative_axes` |
| `provenance` | Third-party source, license, version, and commit ledger | `provenance_ledger`, `provenance_required` |
| `database` | Migration, schema, and worker-parity declaration | `db_migration_check`, `db_schema_check`, `db_worker_parity` |
| `isolation` | Scope registry and spec `scope` declaration | `isolation_registry`, `isolation_scopes`, `isolation_helper` |
| `api` | Contract inventory, `x-spec`, gap tag, manifest parity | `api_contract_dir`, `api_spec_tag`, `api_gap_tag`, `api_manifest` |
| `security` | Posture, controls, supply chain, scan declarations | `security_level`, `security_controls`, `security_require_threat_model`, `security_lockfile`, `security_sbom`, `security_require_image_digest`, `security_scans` |

## Shipped P2

| Module | Adds | Config keys |
| :--- | :--- | :--- |
| `bands` | Spec band reservations | `bands_size` |
| `epic` | Epic grouping and the registry epic view | — |
| `metrics-export` | JSON metrics export guard | `metrics_out` |
| `matrix` | Combinatorial test matrix registry | `matrix_registry`, `matrix_runner` |

## Enable a module

```yaml
modules: [qa, provenance, matrix]
qa_mode: report
qa_expires: 2026-12-31
qa_defects: DEFECTS.md
provenance_mode: report
provenance_expires: 2026-12-31
provenance_ledger: THIRD_PARTY.md
matrix_mode: report
matrix_expires: 2026-12-31
matrix_registry: matrix_registry.tsv
```

- A module defaults to `off`.
- An enabled module defaults to `report` and requires `<name>_expires`.
- `report` warns. `enforce` blocks on an error.
- A `fatal` finding blocks in both modes. A missing ledger, registry, required
  config, or PyYAML is `fatal`.

## P2 commands

```sh
sdd-gov/g reserve --size 10 --owner "platform team"
sdd-gov/g emit registry --by-epic
sdd-gov/g metrics --out .local/tmp/metrics.json
sdd-gov/g check --hooks
```

## Module interface

A module lives at `governance/modules.d/<name>/`:

- `module.md` — what it adds, configuration, and rules.
- `check.py` — `def check(ctx) -> list[Finding]`.

`ctx` is a dict with `root`, `project_root`, `profile`, `specs`, `tags`, `changed`,
`ledgers`, and `spec_width`. A finding is `(path, message)`,
`(severity, path, message)`, or a severity such as `fatal`.

A module MUST NOT weaken an invariant. A module MUST NOT write a file, run a
network call, or run a project command. Stack commands stay in `PROJECT.md`
`checks:` and run with `check --hooks`.

## Numbering

| Scope | Form | Example |
| :--- | :--- | :--- |
| Spec | `id_width` digits | `0001` or `001` |
| Requirement | `REQ-<spec>-<nn>` | `REQ-0001-01` |
| Task | `T-<spec>-<nn>` | `T-0001-01` |
| Decision | `DEC-<spec>-<nn>` | `DEC-0001-01` |
| Known issue | `KI-<spec>-<nn>` | `KI-0001-01` |
| Defect | `DEF-<nnnn>` | `DEF-0001` |
| Provenance | `TP-<nnnn>` | `TP-0001` |
| Risk | `RISK-<nnnn>` | `RISK-0001` |
| Exception | `EXC-<nnnn>` | `EXC-0001` |
| Work item | `W-<nnnn>` | `W-0001` |
| Matrix | `M-<nnnn>` | `M-0001` |

The check enforces the width. A legacy width is an error.

## Dependency

The `api` module requires PyYAML:

```sh
pip install pyyaml
# or
uv add pyyaml
```

The core stays standard-library only.
