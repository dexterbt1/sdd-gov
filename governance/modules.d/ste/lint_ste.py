#!/usr/bin/env python3
"""A small Simplified Technical English check for Markdown.

This is a heuristic. It finds common problems. It does not replace a human review.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

CONTRACTIONS = re.compile(
    r"\b(?:can't|won't|don't|doesn't|didn't|isn't|aren't|wasn't|weren't|"
    r"hasn't|haven't|hadn't|shouldn't|wouldn't|couldn't|it's|that's|"
    r"there's|what's|let's|i'm|you're|we're|they're|i've|you've|we've|"
    r"they've|i'll|you'll|we'll|they'll|i'd|you'd|we'd|they'd)\b",
    re.IGNORECASE,
)
VAGUE = re.compile(r"\b(handle|manage|process|deal with|support)\b", re.IGNORECASE)
SKIP_PARTS = {".git", "node_modules", ".venv", ".local", "coverage-out"}


def sentences(text):
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith(("#", "|", "```", "<!--")):
            continue
        for sentence in re.split(r"(?<=[.!?])\s+", line):
            sentence = sentence.strip()
            if sentence:
                yield sentence


def lint(path):
    findings = []
    text = path.read_text(encoding="utf-8", errors="ignore")
    for number, line in enumerate(text.splitlines(), 1):
        for match in CONTRACTIONS.finditer(line):
            findings.append("%s:%d: contraction %r" % (path, number, match.group(0)))
        for match in VAGUE.finditer(line):
            findings.append("%s:%d: vague verb %r" % (path, number, match.group(0)))
    for sentence in sentences(text):
        words = len(re.findall(r"\S+", sentence))
        limit = 20 if re.match(r"^(?:\d+\.|-|\*)\s", sentence) else 25
        if words > limit:
            findings.append("%s: sentence has %d words (limit %d): %s" % (path, words, limit, sentence[:60]))
    return findings


def main(argv):
    root = Path(argv[1] if len(argv) > 1 else ".")
    findings = []
    for path in sorted(root.rglob("*.md")):
        if any(part in SKIP_PARTS for part in path.parts):
            continue
        findings.extend(lint(path))
    for finding in findings:
        print(finding)
    if findings:
        print("ste: %d findings" % len(findings))
        return 1
    print("ste: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
