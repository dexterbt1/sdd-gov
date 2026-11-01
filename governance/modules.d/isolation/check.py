"""Isolation scope registry check."""

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
    registry_value = str(profile.get("isolation_registry", "isolation/scopes.json"))
    registry = root / registry_value
    if not registry.exists():
        return [("fatal", registry_value, "isolation registry not found")]
    try:
        data = json.loads(registry.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [("fatal", registry_value, "invalid isolation registry: %s" % exc)]

    allowed = [str(item) for item in as_list(
        profile.get("isolation_scopes", ["workspace", "account", "global", "none"])
    )]
    findings = []
    seen = set()
    tables = data.get("tables", [])
    if not isinstance(tables, list):
        return [("fatal", registry_value, "tables must be a list")]
    for table in tables:
        if not isinstance(table, dict):
            findings.append((registry_value, "table entry must be an object"))
            continue
        name = str(table.get("table", "")).strip()
        scope = str(table.get("scope", "")).strip()
        if not name:
            findings.append((registry_value, "table entry without a name"))
            continue
        if name in seen:
            findings.append((registry_value, "duplicate table %s" % name))
        seen.add(name)
        if scope not in allowed:
            findings.append((registry_value, "%s has invalid scope %s" % (name, scope)))

    helper_value = profile.get("isolation_helper")
    if helper_value and not (root / str(helper_value)).exists():
        findings.append(("fatal", str(helper_value), "isolation helper not found"))

    for spec in specs:
        scope = spec["fm"].get("scope")
        if scope is not None and str(scope) not in allowed:
            findings.append((spec["rel"], "invalid spec scope %s" % scope))
    return findings
