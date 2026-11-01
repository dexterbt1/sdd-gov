# Module: epic

## Purpose

Keep the epic grouping complete and make the epic view useful.

## Enable

```yaml
modules: [epic]
epic_mode: report
epic_expires: 2026-12-31
```

## Registry view

```sh
sdd-gov/g emit registry --by-epic
```

The registry includes an `Epic` column, and `--by-epic` groups the rows by epic.

## Check

- A spec in `specified`, `in_progress`, or `completed` has a non-empty `epic`.
- A draft, planned, or reserved spec MAY omit the epic.
