"""Combinatorial test matrix registry check."""

import re
from pathlib import Path

MATRIX_ID = re.compile(r"^M-\d{4}$")


def as_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def check(ctx):
    root = Path(ctx["root"])
    profile = ctx["profile"]
    registry_value = str(profile.get("matrix_registry", "matrix_registry.tsv"))
    registry = root / registry_value
    if not registry.exists():
        return [("fatal", registry_value, "matrix registry not found")]

    lines = [
        line
        for line in registry.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    if not lines:
        return [("fatal", registry_value, "matrix registry is empty")]
    header = [cell.strip() for cell in lines[0].split("\t")]
    required = ["id", "axis", "values", "baseline"]
    missing = [column for column in required if column not in header]
    if missing:
        return [("fatal", registry_value, "header missing %s" % ", ".join(missing))]

    findings = []
    seen = set()
    for number, line in enumerate(lines[1:], 2):
        cells = [cell.strip() for cell in line.split("\t")]
        if len(cells) < len(header):
            cells += [""] * (len(header) - len(cells))
        row = dict(zip(header, cells))
        matrix_id = row.get("id", "").strip()
        if not MATRIX_ID.match(matrix_id):
            findings.append((registry_value, "row %d: invalid id %s" % (number, matrix_id)))
        if matrix_id in seen:
            findings.append((registry_value, "duplicate matrix id %s" % matrix_id))
        seen.add(matrix_id)
        axis = row.get("axis", "").strip()
        values = [value.strip() for value in row.get("values", "").split(",") if value.strip()]
        baseline = row.get("baseline", "").strip()
        if not axis:
            findings.append((registry_value, "%s has no axis" % matrix_id))
        if len(values) < 2:
            findings.append((registry_value, "%s needs at least two values" % matrix_id))
        if baseline not in values:
            findings.append(
                (registry_value, "%s baseline %s is not in values" % (matrix_id, baseline))
            )

    runner = profile.get("matrix_runner")
    if runner:
        hooks = [str(item).strip() for item in as_list(profile.get("checks"))]
        if str(runner).strip() not in hooks:
            findings.append(("PROJECT.md", "matrix_runner is not in checks"))
    return findings
