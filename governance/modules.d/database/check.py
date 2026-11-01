"""Database safety declaration check."""

def as_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def check(ctx):
    profile = ctx["profile"]
    declared = []
    for key in ("db_migration_check", "db_schema_check", "db_worker_parity"):
        value = str(profile.get(key, "")).strip()
        if value:
            declared.append((key, value))

    findings = []
    if not str(profile.get("db_migration_check", "")).strip():
        findings.append(("fatal", "PROJECT.md", "database is enabled; db_migration_check is required"))

    hooks = [str(item).strip() for item in as_list(profile.get("checks"))]
    for key, value in declared:
        if value not in hooks:
            findings.append(
                ("PROJECT.md", "%s is declared but is not in checks: %s" % (key, value))
            )
    return findings
