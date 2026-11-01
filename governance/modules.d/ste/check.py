"""Simplified Technical English check."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lint_ste  # noqa: E402


def check(ctx):
    root = Path(ctx["root"])
    targets = list((root / "specs").glob("*.md"))
    targets += [
        root / name
        for name in ("DECISIONS.md", "KNOWN_ISSUES.md", "RISKS.md", "WORK.md", "MEMORY.md")
    ]
    findings = []
    for path in targets:
        if not path.exists():
            continue
        for finding in lint_ste.lint(path):
            findings.append((str(path.relative_to(root)), finding))
    return findings
