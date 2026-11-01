# Module: provenance

## Purpose

Keep one ledger for every third-party skill, dependency, image, and tool.

## Enable

```yaml
modules: [provenance]
provenance_mode: report
provenance_expires: 2026-12-31
provenance_ledger: THIRD_PARTY.md
provenance_required: [source, license, version, commit]
```

## Ledger

| ID | Name | Kind | Source | Version | Commit | License | Scope |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| TP-0001 | example-skill | skill | https://example.com/skill | 1.0.0 | abc123 | MIT | vendored |

- `ID` is `TP-<nnnn>`.
- `Kind` is `skill`, `dependency`, `image`, or `tool`.
- `Scope` is `vendored`, `adapted`, or `dev`.
- Every required field MUST be present.
- A duplicate ID or a missing license is an error.

## Check

- A missing ledger is `fatal`.
- A missing required field is an error.
- A source MUST be a URL or a path.
