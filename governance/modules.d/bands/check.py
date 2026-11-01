"""Spec band reservation check."""

import json
from pathlib import Path


def check(ctx):
    root = Path(ctx["root"])
    profile = ctx["profile"]
    path = root / "governance" / "reservations.json"
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [("fatal", "governance/reservations.json", "invalid JSON: %s" % exc)]

    bands = data.get("bands", [])
    if not isinstance(bands, list):
        return [("fatal", "governance/reservations.json", "bands must be a list")]
    size = int(profile.get("bands_size", 10) or 10)
    findings = []
    ranges = []
    for band in bands:
        if not isinstance(band, dict):
            findings.append(("governance/reservations.json", "band must be an object"))
            continue
        try:
            start = int(band.get("start"))
            end = int(band.get("end"))
        except (TypeError, ValueError):
            findings.append(("governance/reservations.json", "band needs integer start and end"))
            continue
        owner = str(band.get("owner", "")).strip()
        if start > end:
            findings.append(("governance/reservations.json", "band start %d exceeds end %d" % (start, end)))
        if end - start + 1 > size:
            findings.append(
                ("governance/reservations.json", "band %d-%d exceeds bands_size %d" % (start, end, size))
            )
        if not owner:
            findings.append(("governance/reservations.json", "band %d-%d has no owner" % (start, end)))
        ranges.append((start, end))

    ranges.sort()
    for index in range(1, len(ranges)):
        if ranges[index][0] <= ranges[index - 1][1]:
            findings.append(
                (
                    "governance/reservations.json",
                    "band %d-%d overlaps %d-%d"
                    % (ranges[index][0], ranges[index][1], ranges[index - 1][0], ranges[index - 1][1]),
                )
            )

    for value in data.get("reserved", []):
        try:
            reserved = int(value)
        except (TypeError, ValueError):
            continue
        for start, end in ranges:
            if start <= reserved <= end:
                findings.append(
                    (
                        "governance/reservations.json",
                        "reserved id %d falls inside band %d-%d" % (reserved, start, end),
                    )
                )
    return findings
