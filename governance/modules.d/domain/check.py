"""Domain entity registry check."""

import json
from pathlib import Path


def as_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def check(ctx):
    root = Path(ctx["root"])
    profile = ctx["profile"]
    specs = ctx["specs"]
    registry_value = profile.get("domain_registry", "contracts/domain/entities.json")
    registry = root / str(registry_value)
    if not registry.exists():
        return [("fatal", str(registry_value), "domain registry not found")]
    try:
        data = json.loads(registry.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [("fatal", str(registry_value), "invalid registry: %s" % exc)]

    entities = data.get("entities", [])
    if not isinstance(entities, list):
        return [("fatal", str(registry_value), "entities must be a list")]

    spec_ids = {spec["id"] for spec in specs if isinstance(spec["id"], int)}
    findings = []
    names = set()
    for entity in entities:
        if not isinstance(entity, dict):
            findings.append((str(registry_value), "entity must be an object"))
            continue
        name = str(entity.get("name", "")).strip()
        if not name:
            findings.append((str(registry_value), "entity without name"))
            continue
        if name in names:
            findings.append((str(registry_value), "duplicate entity %s" % name))
        names.add(name)
        if not str(entity.get("kind", "")).strip():
            findings.append((str(registry_value), "%s missing kind" % name))
        if entity.get("scope") not in ("workspace", "account", "global", "none", None):
            findings.append((str(registry_value), "%s has invalid scope" % name))
        owning = entity.get("owning_spec")
        if owning is not None:
            try:
                if int(owning) not in spec_ids:
                    findings.append(
                        (str(registry_value), "%s has unknown owning_spec %s" % (name, owning))
                    )
            except (TypeError, ValueError):
                findings.append(
                    (str(registry_value), "%s has invalid owning_spec" % name)
                )

    for spec in specs:
        for name in as_list(spec["fm"].get("entities")):
            if str(name) not in names:
                findings.append((spec["rel"], "unknown entity %s" % name))

    doc_value = profile.get("domain_doc")
    if doc_value:
        doc = root / str(doc_value)
        if not doc.exists():
            findings.append((str(doc_value), "domain document not found"))

    return findings
