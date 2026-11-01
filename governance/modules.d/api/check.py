"""OpenAPI contract inventory and traceability check."""

import json
import re
from pathlib import Path

METHODS = {"get", "post", "put", "patch", "delete", "head", "options", "trace"}
GAP_ID = re.compile(r"^(?:GAP|G)-[A-Z0-9-]+$")


def as_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def list_operations(data):
    operations = []
    paths = data.get("paths") if isinstance(data, dict) else None
    if not isinstance(paths, dict):
        return operations
    for path, item in paths.items():
        if not isinstance(item, dict):
            continue
        for method, operation in item.items():
            if method.lower() in METHODS and isinstance(operation, dict):
                operations.append((path, method.lower(), operation))
    return operations


def check(ctx):
    try:
        import yaml
    except ImportError:
        return [
            (
                "fatal",
                "api",
                "PyYAML is required; install it with `pip install pyyaml` or `uv add pyyaml`",
            )
        ]

    root = Path(ctx["root"])
    profile = ctx["profile"]
    specs = ctx["specs"]
    contract_value = str(profile.get("api_contract_dir", "contracts/api"))
    contract_dir = root / contract_value
    if not contract_dir.exists():
        return [("fatal", contract_value, "contract directory not found")]

    spec_tag = str(profile.get("api_spec_tag", "x-spec"))
    gap_tag = str(profile.get("api_gap_tag", "x-gap"))
    req_ids = {req["id"] for spec in specs for req in spec["reqs"]}
    findings = []

    files = sorted(
        [
            path
            for path in contract_dir.rglob("*")
            if path.is_file() and path.suffix.lower() in (".yaml", ".yml", ".json")
        ]
    )
    if not files:
        findings.append((contract_value, "no contract files found"))

    for path in files:
        rel_path = str(path.relative_to(root))
        try:
            if path.suffix.lower() == ".json":
                data = json.loads(path.read_text(encoding="utf-8"))
            else:
                data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except Exception as exc:  # noqa: BLE001
            findings.append((rel_path, "invalid contract: %s" % exc))
            continue
        operations = list_operations(data)
        for operation_path, method, operation in operations:
            tag = operation.get(spec_tag)
            if not tag:
                findings.append(
                    (rel_path, "%s %s has no %s" % (method.upper(), operation_path, spec_tag))
                )
                continue
            for raw_ref in as_list(tag):
                if isinstance(raw_ref, dict):
                    raw_ref = raw_ref.get("req") or raw_ref.get("id")
                ref = str(raw_ref).strip()
                if not ref.startswith("REQ-"):
                    findings.append((rel_path, "invalid %s value %s" % (spec_tag, ref)))
                elif ref not in req_ids:
                    findings.append((rel_path, "%s %s does not resolve" % (spec_tag, ref)))
            gap = operation.get(gap_tag)
            if gap and str(gap).strip() not in ("", "—", "-"):
                if not GAP_ID.match(str(gap).strip()):
                    findings.append((rel_path, "invalid %s value %s" % (gap_tag, gap)))

    manifest_value = profile.get("api_manifest")
    if manifest_value:
        manifest = root / str(manifest_value)
        if not manifest.exists():
            findings.append(("fatal", str(manifest_value), "contract manifest not found"))
        else:
            try:
                data = json.loads(manifest.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                findings.append(("fatal", str(manifest_value), "invalid manifest: %s" % exc))
                return findings
            listed = {
                str(entry.get("file", "")).strip()
                for entry in data.get("contracts", [])
                if isinstance(entry, dict)
            }
            for path in files:
                rel_path = str(path.relative_to(root))
                if rel_path not in listed:
                    findings.append(
                        (str(manifest_value), "contract %s is missing from the manifest" % rel_path)
                    )
            for rel_path in listed:
                if rel_path and not (root / rel_path).exists():
                    findings.append(
                        (str(manifest_value), "manifest lists a missing file %s" % rel_path)
                    )
    return findings
