"""Epic grouping check."""

def check(ctx):
    findings = []
    for spec in ctx["specs"]:
        if spec["status"] not in ("specified", "in_progress", "completed"):
            continue
        value = spec["fm"].get("epic")
        if (
            value is None
            or (isinstance(value, list) and not value)
            or str(value).strip() == ""
        ):
            findings.append((spec["rel"], "missing epic"))
    return findings
