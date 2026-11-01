"""Metrics export guard."""

import json
from pathlib import Path


def check(ctx):
    project_root = Path(ctx["project_root"]).resolve()
    profile = ctx["profile"]
    out_value = profile.get("metrics_out")
    if not out_value:
        return [("fatal", "PROJECT.md", "metrics-export is enabled; metrics_out is required")]

    target = (project_root / str(out_value)).resolve()
    if not (target == project_root or project_root in target.parents):
        return [("fatal", str(out_value), "metrics_out must stay inside the project root")]
    if not target.exists():
        return [
            (
                "fatal",
                str(out_value),
                "metrics export not found; run `govern.py metrics --out %s`" % out_value,
            )
        ]
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [("fatal", str(out_value), "metrics export is not valid JSON: %s" % exc)]
    if not isinstance(data, dict):
        return [("fatal", str(out_value), "metrics export must be a JSON object")]

    newest = 0
    for spec in ctx["specs"]:
        try:
            newest = max(newest, spec["path"].stat().st_mtime)
        except OSError:
            pass
    if newest > target.stat().st_mtime:
        return [(str(out_value), "metrics export is stale; re-run the export")]
    return []
