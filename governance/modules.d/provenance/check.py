"""Third-party provenance ledger check."""

import re
from pathlib import Path

PROVENANCE_ID = re.compile(r"^TP-\d{4}$")
KINDS = {"skill", "dependency", "image", "tool"}
SCOPES = {"vendored", "adapted", "dev"}


def as_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def load_table(path):
    lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip().startswith("|")]
    header = None
    rows = []
    for line in lines:
        cells = [cell.strip().strip("`") for cell in line.strip().strip("|").split("|")]
        if all(re.fullmatch(r":?-{2,}:?", cell) for cell in cells if cell):
            continue
        if header is None:
            header = [re.sub(r"[^a-z0-9]+", "_", cell.lower()).strip("_") for cell in cells]
            continue
        if len(cells) < len(header):
            cells += [""] * (len(header) - len(cells))
        rows.append(dict(zip(header, cells)))
    return rows


def check(ctx):
    root = Path(ctx["root"])
    profile = ctx["profile"]
    ledger_value = str(profile.get("provenance_ledger", "THIRD_PARTY.md"))
    ledger = root / ledger_value
    if not ledger.exists():
        return [("fatal", ledger_value, "provenance ledger not found")]

    required = [str(item) for item in as_list(
        profile.get("provenance_required", ["source", "license", "version", "commit"])
    )]
    findings = []
    seen = set()
    for row in load_table(ledger):
        artifact = row.get("id", "").strip()
        if not artifact:
            continue
        if not PROVENANCE_ID.match(artifact):
            findings.append((ledger_value, "invalid provenance id %s" % artifact))
        if artifact in seen:
            findings.append((ledger_value, "duplicate provenance id %s" % artifact))
        seen.add(artifact)
        for field in required:
            if not row.get(field, "").strip():
                findings.append((ledger_value, "%s missing %s" % (artifact, field)))
        kind = row.get("kind", "").strip().lower()
        if kind and kind not in KINDS:
            findings.append((ledger_value, "%s has invalid kind %s" % (artifact, kind)))
        scope = row.get("scope", "").strip().lower()
        if scope and scope not in SCOPES:
            findings.append((ledger_value, "%s has invalid scope %s" % (artifact, scope)))
        source = row.get("source", "").strip()
        if source and not (source.startswith("http://") or source.startswith("https://") or "/" in source):
            findings.append((ledger_value, "%s source must be a URL or a path" % artifact))
    return findings
