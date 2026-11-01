# Module: api

## Purpose

Keep a contract inventory and make traceability explicit for every operation.

## Enable

```yaml
modules: [api]
api_mode: report
api_expires: 2026-12-31
api_contract_dir: contracts/api
api_spec_tag: x-spec
api_gap_tag: x-gap
api_manifest: contracts/api/coverage.json
```

## Dependency

The `api` module requires PyYAML:

```sh
pip install pyyaml
# or
uv add pyyaml
```

The core itself stays standard-library only.

## Contract rules

- Every operation has `x-spec`.
- `x-spec` is a `REQ-<spec>-<nn>` ID or a list of them.
- Every `x-spec` resolves to a requirement.
- `x-gap` is optional. When present, it uses the `GAP-...` or `G-...` form.
- When `api_manifest` is set, every contract file appears in the manifest and every
  manifest entry exists.

## Manifest

```json
{
  "contracts": [
    { "file": "contracts/api/core-admin.yaml", "spec": 1 }
  ]
}
```

## Check

- Missing PyYAML, a missing contract directory, or a missing manifest is `fatal`.
- An operation without `x-spec`, an unknown `x-spec`, or a manifest mismatch is an error.
