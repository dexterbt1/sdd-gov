# Module: isolation

## Purpose

Make workspace, account, and global scope explicit.

## Enable

```yaml
modules: [isolation]
isolation_mode: report
isolation_expires: 2026-12-31
isolation_registry: isolation/scopes.json
isolation_scopes: [workspace, account, global, none]
isolation_helper: path/to/scoped_query.py
```

## Registry

```json
{
  "tables": [
    { "table": "users", "scope": "global" },
    { "table": "workspaces", "scope": "account" },
    { "table": "approval_requests", "scope": "workspace" }
  ]
}
```

A spec MAY declare `scope: workspace`, `account`, `global`, or `none`.

## Check

- A missing registry or helper is `fatal`.
- An unknown table scope, a duplicate table, or an invalid spec scope is an error.
- The module does not scan a query. A project hook scans the scoped queries.
