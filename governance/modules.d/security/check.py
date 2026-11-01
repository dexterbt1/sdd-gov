"""Security posture and declaration check."""

import json
import re
from pathlib import Path

LEVELS = {"P0", "P1", "P2", "P3", "P4"}
SCANS = {"secret", "sast", "sca", "iac", "container"}
IMAGE = re.compile(r"^\s*image:\s*(\S+)")


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
    level = str(profile.get("security_level", "P1")).upper()
    if level not in LEVELS:
        return [("fatal", "PROJECT.md", "security_level must be P0 through P4")]

    findings = []
    if bool(profile.get("security_require_threat_model", True)):
        for spec in specs:
            if spec["fm"].get("trust_boundary") is True:
                if "## Threat Model" not in spec["body"]:
                    findings.append((spec["rel"], "trust boundary needs ## Threat Model"))
                if "## Security Impact" not in spec["body"]:
                    findings.append((spec["rel"], "trust boundary needs ## Security Impact"))

    controls_value = profile.get("security_controls")
    if controls_value:
        controls = root / str(controls_value)
        if not controls.exists():
            findings.append(("fatal", str(controls_value), "control registry not found"))
        else:
            try:
                data = json.loads(controls.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                findings.append(("fatal", str(controls_value), "invalid control registry: %s" % exc))
                data = {}
            for control in data.get("controls", []):
                if not isinstance(control, dict):
                    findings.append((str(controls_value), "control must be an object"))
                    continue
                control_id = str(control.get("id", "")).strip() or "?"
                for field in ("id", "owner", "gate"):
                    if not str(control.get(field, "")).strip():
                        findings.append(
                            (str(controls_value), "%s missing %s" % (control_id, field))
                        )

    lockfile = profile.get("security_lockfile")
    if lockfile and not (root / str(lockfile)).exists():
        findings.append((str(lockfile), "lock file not found"))

    sbom = profile.get("security_sbom")
    if sbom and not (root / str(sbom)).exists():
        findings.append((str(sbom), "SBOM not found"))

    if bool(profile.get("security_require_image_digest", False)):
        candidates = []
        for pattern in ("compose*.yaml", "compose*.yml", "Dockerfile*"):
            candidates.extend(root.rglob(pattern))
        for path in candidates:
            if not path.is_file():
                continue
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                match = IMAGE.match(line)
                if match and "@sha256:" not in match.group(1):
                    findings.append(
                        (
                            str(path.relative_to(root)),
                            "line %d: image without a sha256 digest" % number,
                        )
                    )

    scans = [str(item).strip().lower() for item in as_list(profile.get("security_scans", []))]
    for scan in scans:
        if scan and scan not in SCANS:
            findings.append(("PROJECT.md", "unknown security scan %s" % scan))
    return findings
