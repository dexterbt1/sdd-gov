# Module: database

## Purpose

Make the database safety checks explicit and run them in the project root.

## Enable

```yaml
modules: [database]
database_mode: report
database_expires: 2026-12-31
db_migration_check: "alembic check"
db_schema_check: "python3 scripts/verify_schema_acyclic.py"
db_worker_parity: "python3 scripts/verify_worker_parity.py"
```

Add the same commands to `PROJECT.md` `checks:` so `check --hooks` runs them.

## Check

- `db_migration_check` is required. A missing value is `fatal`.
- Each declared command MUST appear in `PROJECT.md` `checks:`.
- The module does not run a command itself. The core runs the hooks in the
  project root.

## Rules

- A migration change MUST keep `alembic check` clean.
- A new backend layer MUST keep the schema acyclic.
- A worker command MUST keep the deployment worker parity.
