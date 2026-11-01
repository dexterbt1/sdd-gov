# Module: matrix

## Purpose

Keep a combinatorial test matrix registry with a safe baseline.

## Enable

```yaml
modules: [matrix]
matrix_mode: report
matrix_expires: 2026-12-31
matrix_registry: matrix_registry.tsv
matrix_runner: "scripts/run-matrix.sh"
```

## Registry

A tab-separated file with a header row:

```
id	axis	values	baseline
M-0001	provider	aws,github,gitlab	aws
M-0002	region	us,eu	us
```

- `ID` is `M-<nnnn>`.
- `values` is a comma-separated list with at least two values.
- `baseline` is one of the values.
- `axis` is non-empty.

## Runner

Add `matrix_runner` to `PROJECT.md` `checks:` and run `check --hooks`. The module
does not run the matrix.

## Check

- The registry exists and has the required header.
- Every row has a valid ID, a non-empty axis, at least two values, and a baseline
  that is one of the values.
- `matrix_runner`, when set, appears in `checks:`.
