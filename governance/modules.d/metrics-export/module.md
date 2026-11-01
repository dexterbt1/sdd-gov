# Module: metrics-export

## Purpose

Keep a JSON metrics export for an external dashboard.

## Enable

```yaml
modules: [metrics-export]
metrics-export_mode: report
metrics-export_expires: 2026-12-31
metrics_out: .local/tmp/metrics.json
```

## Export

```sh
sdd-gov/g metrics --out .local/tmp/metrics.json
```

The output is JSON with `generated`, `specs`, `completed`, `requirements`,
`traceability`, `decisions`, `known_issues_open`, `risks_open`, and
`lead_time_days_avg`.

## Check

- `metrics_out` is set.
- The target stays inside the project root.
- The file exists and is valid JSON.
- The file is not older than the newest spec.

The module does not write the file. The `metrics --out` command does.
