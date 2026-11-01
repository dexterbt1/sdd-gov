# Module: domain

## Purpose

Keep a single entity registry and reject an unknown or duplicate entity.

## Enable

```yaml
modules: [domain]
domain_mode: enforce
domain_registry: contracts/domain/entities.json
domain_doc: doc/architecture/domain-model.md
```

## Registry shape

```json
{
  "entities": [
    {
      "name": "Account",
      "kind": "aggregate",
      "scope": "account",
      "owning_spec": 1
    }
  ]
}
```

## Rules

- The registry exists when the module is enabled.
- Each entity has a unique `name`, a `kind`, and a `scope`.
- `scope` is `workspace`, `account`, `global`, or `none`.
- `owning_spec` resolves to a spec.
- A spec `entities:` entry resolves to a registered entity.
- If `domain_doc` is set, the file exists.

## Check

`check.py` validates the registry and the spec references. It does not scan an ORM.
A project hook can scan the ORM and compare its models to the registry.
